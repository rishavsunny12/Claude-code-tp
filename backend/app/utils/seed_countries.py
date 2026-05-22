"""
Seed the countries table with the top 60 food-insecure countries.
Data: ISO 3166-1 alpha-3 codes with centroids.
Run once on first boot or with: python -m app.utils.seed_countries
"""

COUNTRIES = [
    # Sub-Saharan Africa (highest food insecurity risk)
    ("ETH", "Ethiopia",               9.1450,  40.4897),
    ("SOM", "Somalia",                5.1521,  46.1996),
    ("SDN", "Sudan",                  12.8628, 30.2176),
    ("SSD", "South Sudan",            6.8770,  31.3070),
    ("NER", "Niger",                  17.6078, 8.0817),
    ("MLI", "Mali",                   17.5707, -3.9962),
    ("BFA", "Burkina Faso",           12.3641, -1.5275),
    ("TCD", "Chad",                   15.4542, 18.7322),
    ("CAF", "Central African Republic", 6.6111, 20.9394),
    ("COD", "DR Congo",               -4.0383, 21.7587),
    ("ZWE", "Zimbabwe",               -19.0154, 29.1549),
    ("MOZ", "Mozambique",             -18.6657, 35.5296),
    ("ZMB", "Zambia",                 -13.1339, 27.8493),
    ("MDG", "Madagascar",             -18.7669, 46.8691),
    ("MWI", "Malawi",                 -13.2543, 34.3015),
    ("KEN", "Kenya",                  -0.0236, 37.9062),
    ("TZA", "Tanzania",               -6.3690, 34.8888),
    ("UGA", "Uganda",                 1.3733,  32.2903),
    ("RWA", "Rwanda",                 -1.9403, 29.8739),
    ("BDI", "Burundi",                -3.3731, 29.9189),
    ("ERI", "Eritrea",                15.1794, 39.7823),
    ("DJI", "Djibouti",               11.8251, 42.5903),
    ("GIN", "Guinea",                 11.0041, -10.9408),
    ("SLE", "Sierra Leone",           8.4606,  -11.7799),
    ("LBR", "Liberia",                6.4281,  -9.4295),
    ("CMR", "Cameroon",               3.8480,  11.5021),
    ("NGA", "Nigeria",                9.0820,  8.6753),
    ("GHA", "Ghana",                  7.9465,  -1.0232),
    ("SEN", "Senegal",                14.4974, -14.4524),
    ("MRT", "Mauritania",             21.0079, -10.9408),
    # South/South-East Asia
    ("AFG", "Afghanistan",            33.9391, 67.7100),
    ("BGD", "Bangladesh",             23.6850, 90.3563),
    ("NPL", "Nepal",                  28.3949, 84.1240),
    ("MMR", "Myanmar",                21.9162, 95.9560),
    ("KHM", "Cambodia",               12.5657, 104.9910),
    ("PRK", "North Korea",            40.3399, 127.5101),
    ("HTI", "Haiti",                  18.9712, -72.2852),
    ("GTM", "Guatemala",              15.7835, -90.2308),
    ("HND", "Honduras",               15.1999, -86.2419),
    ("NIC", "Nicaragua",              12.8654, -85.2072),
    ("BOL", "Bolivia",                -16.2902, -63.5887),
    ("VEN", "Venezuela",              6.4238,  -66.5897),
    ("YEM", "Yemen",                  15.5527, 48.5164),
    ("SYR", "Syria",                  34.8021, 38.9968),
    ("IRQ", "Iraq",                   33.2232, 43.6793),
    ("PSE", "Palestine",              31.9522, 35.2332),
    ("LBN", "Lebanon",                33.8547, 35.8623),
    ("PAK", "Pakistan",               30.3753, 69.3451),
    ("IND", "India",                  20.5937, 78.9629),
    ("IDN", "Indonesia",              -0.7893, 113.9213),
    ("PNG", "Papua New Guinea",       -6.3149, 143.9555),
    ("TLS", "Timor-Leste",            -8.8742, 125.7275),
    ("UKR", "Ukraine",                48.3794, 31.1656),
    ("MDV", "Maldives",               3.2028,  73.2207),
    ("LKA", "Sri Lanka",              7.8731,  80.7718),
    ("PHL", "Philippines",            12.8797, 121.7740),
    ("COL", "Colombia",               4.5709,  -74.2973),
    ("PER", "Peru",                   -9.1900, -75.0152),
    ("ECU", "Ecuador",                -1.8312, -78.1834),
    ("ZAF", "South Africa",           -30.5595, 22.9375),
    ("AGO", "Angola",                 -11.2027, 17.8739),
]


async def seed_countries(db):
    """Insert countries if not already present."""
    from sqlalchemy import select
    from app.models.country import Country

    result = await db.execute(select(Country.iso_code))
    existing = set(result.scalars().all())

    new_countries = []
    for iso, name, lat, lon in COUNTRIES:
        if iso not in existing:
            new_countries.append(Country(iso_code=iso, name=name, latitude=lat, longitude=lon))

    if new_countries:
        db.add_all(new_countries)
        await db.commit()
        print(f"Seeded {len(new_countries)} countries")
    else:
        print("Countries already seeded")
