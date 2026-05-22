"""
Data ingestion orchestrator.
Fetches fresh data from all real external sources and upserts into the database.
Called by the scheduler and the admin refresh endpoint.
"""

import logging
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.ndvi_data import NDVIData
from app.models.rainfall_data import RainfallData
from app.models.alert import Alert
from app.services.data.hunger_map import fetch_all_countries
from app.services.data.open_meteo import fetch_monthly_rainfall
from app.services.data.nasa_ndvi import fetch_ndvi_from_modis_api, compute_ndvi_anomaly
from app.services.data.chirps_rainfall import compute_anomaly
from app.services.analysis.risk_scorer import compute_risk_score
from app.services.analysis.alert_engine import evaluate_alerts

logger = logging.getLogger(__name__)


async def run_full_refresh(db: AsyncSession) -> dict:
    """Run a full data refresh: WFP → weather → NDVI → risk scores → alerts."""
    stats = {"countries_updated": 0, "alerts_generated": 0, "errors": []}

    # Fetch WFP HungerMap data for all countries
    logger.info("Fetching WFP HungerMap data...")
    hunger_map_data = await fetch_all_countries()
    hunger_map_index = {c.iso_code: c for c in hunger_map_data}

    # Get all countries from DB
    result = await db.execute(select(Country))
    countries = result.scalars().all()

    today = date.today()
    current_month = date(today.year, today.month, 1)

    for country in countries:
        try:
            wfp = hunger_map_index.get(country.iso_code)

            # Fetch monthly weather/rainfall for this country
            if country.latitude and country.longitude:
                monthly_weather = await fetch_monthly_rainfall(
                    lat=country.latitude,
                    lon=country.longitude,
                    start=date(today.year - 1, today.month, 1),
                    end=today,
                )
            else:
                monthly_weather = []

            # Upsert rainfall data and compute anomaly
            latest_rainfall = None
            if monthly_weather:
                # Compute baseline from all historical months except last 3
                historical = monthly_weather[:-3] if len(monthly_weather) > 3 else []
                baseline_by_month: dict[int, list[float]] = {}
                for record in historical:
                    m = record.date.month
                    baseline_by_month.setdefault(m, []).append(record.total_precipitation_mm)

                for weather_record in monthly_weather[-3:]:  # upsert last 3 months
                    baseline = baseline_by_month.get(weather_record.date.month, [])
                    anomaly = compute_anomaly(weather_record.total_precipitation_mm, baseline)

                    await db.execute(
                        pg_insert(RainfallData)
                        .values(
                            country_id=country.id,
                            date=weather_record.date,
                            rainfall_mm=weather_record.total_precipitation_mm,
                            anomaly_pct=anomaly,
                        )
                        .on_conflict_do_update(
                            constraint="rainfall_data_country_id_date_key",
                            set_={"rainfall_mm": weather_record.total_precipitation_mm, "anomaly_pct": anomaly},
                        )
                    )
                    if weather_record.date >= current_month:
                        latest_rainfall = {"mm": weather_record.total_precipitation_mm, "anomaly": anomaly}

            # Fetch NDVI for this country
            latest_ndvi = None
            if country.latitude and country.longitude:
                ndvi_records = await fetch_ndvi_from_modis_api(
                    iso_code=country.iso_code,
                    lat=country.latitude,
                    lon=country.longitude,
                    start=date(today.year - 1, today.month, 1),
                    end=today,
                )
                if ndvi_records:
                    # Compute anomaly from historical
                    historical_ndvi = ndvi_records[:-2]
                    baseline_ndvi = [r.ndvi_mean for r in historical_ndvi]
                    for ndvi_record in ndvi_records[-2:]:
                        anomaly = compute_ndvi_anomaly(ndvi_record.ndvi_mean, baseline_ndvi)
                        await db.execute(
                            pg_insert(NDVIData)
                            .values(
                                country_id=country.id,
                                date=ndvi_record.date,
                                ndvi_mean=ndvi_record.ndvi_mean,
                                ndvi_anomaly=anomaly,
                            )
                            .on_conflict_do_update(
                                constraint="ndvi_data_country_id_date_key",
                                set_={"ndvi_mean": ndvi_record.ndvi_mean, "ndvi_anomaly": anomaly},
                            )
                        )
                    last = ndvi_records[-1]
                    latest_ndvi = {"mean": last.ndvi_mean, "anomaly": compute_ndvi_anomaly(last.ndvi_mean, baseline_ndvi)}

            # Fetch previous risk score for trend calculation
            prev_result = await db.execute(
                select(RiskScore)
                .where(RiskScore.country_id == country.id)
                .order_by(desc(RiskScore.computed_at))
                .limit(1)
            )
            prev_score_obj = prev_result.scalar_one_or_none()
            prev_score = prev_score_obj.score if prev_score_obj else None

            # Compute composite risk score
            score_result = compute_risk_score(
                ndvi_anomaly=latest_ndvi["anomaly"] if latest_ndvi else None,
                rainfall_anomaly_pct=latest_rainfall["anomaly"] if latest_rainfall else None,
                ipc_phase=wfp.ipc_phase if wfp else None,
                prev_score=prev_score,
            )

            new_score = RiskScore(
                country_id=country.id,
                score=score_result.score,
                ipc_phase=wfp.ipc_phase if wfp else score_result.ipc_equivalent,
                affected_pop=wfp.affected_pop if wfp else None,
                trend=score_result.trend,
                factors=score_result.factors,
            )
            db.add(new_score)

            # Generate alerts if warranted
            new_alerts = evaluate_alerts(
                iso_code=country.iso_code,
                country_name=country.name,
                current_score=score_result.score,
                prev_score=prev_score,
                ipc_phase=wfp.ipc_phase if wfp else None,
                ndvi_anomaly=latest_ndvi["anomaly"] if latest_ndvi else None,
                rainfall_anomaly_pct=latest_rainfall["anomaly"] if latest_rainfall else None,
                affected_pop=wfp.affected_pop if wfp else None,
            )
            for gen_alert in new_alerts:
                db.add(Alert(
                    country_id=country.id,
                    severity=gen_alert.severity,
                    message=gen_alert.message,
                ))
            stats["alerts_generated"] += len(new_alerts)
            stats["countries_updated"] += 1

        except Exception as e:
            logger.exception("Error processing %s: %s", country.iso_code, e)
            stats["errors"].append(f"{country.iso_code}: {str(e)}")

    await db.commit()
    logger.info("Refresh complete: %s", stats)
    return stats
