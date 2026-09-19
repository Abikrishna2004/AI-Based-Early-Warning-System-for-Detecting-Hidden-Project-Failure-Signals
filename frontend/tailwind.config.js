/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0B1220',
        card: '#131B2E',
        border: '#232E47',
        primaryText: '#E8ECF4',
        mutedText: '#8B95AC',
        signal: '#FF8A3D',
        riskLow: '#34D399',
        riskMedium: '#FBBF24',
        riskHigh: '#F5544D',
      },
      fontFamily: {
        heading: ['Space Grotesk', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        sm: '6px',
        card: '10px',
      }
    },
  },
  plugins: [],
}
