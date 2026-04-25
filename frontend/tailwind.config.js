/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'navy': {
          900: '#0A1628',
          800: '#1E3A5F',
        },
        'gold': {
          400: '#F4D03F',
          500: '#D4AF37',
        },
        'silver': '#C0C0C0',
        'bronze': '#CD7F32',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}