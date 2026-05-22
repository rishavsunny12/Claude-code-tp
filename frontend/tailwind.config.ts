import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // App surfaces
        surface: {
          primary: '#0F1419',
          secondary: '#1A1F2E',
          card: '#212836',
          hover: '#2A3347',
        },
        // IPC food security phase colors
        phase: {
          1: '#00AC46',   // Minimal
          2: '#CADD00',   // Stressed
          3: '#E7B000',   // Crisis
          4: '#E35C00',   // Emergency
          5: '#C80000',   // Catastrophe
        },
        // Accent
        accent: {
          DEFAULT: '#01619C',
          light: '#8BB9D2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
