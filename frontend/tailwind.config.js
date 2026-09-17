/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        studio: {
          950: '#090a0f',
          900: '#0f111a',
          850: '#151824',
          800: '#1c2030',
          700: '#282d44',
          600: '#3a4263',
          500: '#5a6594',
          accent: '#6366f1',
          accentHover: '#4f46e5',
          gold: '#f59e0b',
          emerald: '#10b981',
          rose: '#f43f5e',
        }
      }
    },
  },
  plugins: [],
}
