/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          600: '#4f46e5',
          700: '#4338ca',
        },
        ai: '#2563eb',
        success: '#16a34a',
        warning: '#f59e0b',
        danger: '#dc2626',
      },
      borderRadius: {
        card: '8px',
        drawer: '16px',
      },
    },
  },
  plugins: [],
}
