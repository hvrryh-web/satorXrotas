/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        radiant: {
          red: '#ff4655',
          dark: '#0f1419',
          card: '#1a1f2e',
          border: '#2d3748'
        }
      }
    },
  },
  plugins: [],
}
