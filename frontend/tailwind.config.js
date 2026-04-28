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
          950: '#020617', // Deepest Navy
          900: '#0F172A', // Navy background
          800: '#1E293B', // Navy surface
          700: '#334155', // Navy border
        },
        'gold': {
          500: '#C5A059', // Rich Gold
          400: '#D4AF37', // Standard Gold
          300: '#E5C78B', // Champagne
          200: '#F1E4C3', // Cream
        },
        'silver': {
          DEFAULT: '#94A3B8', // Slate Silver
          light: '#CBD5E1',
        },
        'bronze': {
          DEFAULT: '#B45309', // Amber/Bronze
          light: '#D97706',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'], // Outfit is more premium
      },
    },
  },
  plugins: [],
}