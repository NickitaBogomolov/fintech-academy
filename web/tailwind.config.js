/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter Variable"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono Variable"', 'ui-monospace', 'monospace'],
      },
      colors: {
        brand: {
          50: '#eff5ff',
          100: '#dbe8fe',
          200: '#bfd6fe',
          300: '#93bbfd',
          400: '#6098fa',
          500: '#3b76f6',
          600: '#2558eb',
          700: '#1d44d8',
          800: '#1e39af',
          900: '#1e348a',
        },
        ink: {
          50: '#f7f8fa',
          100: '#eef0f4',
          200: '#dde1e8',
          300: '#c3c9d4',
          400: '#9aa3b2',
          500: '#6b7487',
          600: '#4e5668',
          700: '#3a4152',
          800: '#252b38',
          900: '#141824',
        },
        good: '#0ca30c',
        warn: '#b77800',
        bad: '#d03b3b',
        series: { 1: '#2a78d6', 2: '#eb6834' },
      },
      boxShadow: {
        card: '0 1px 2px rgba(20, 24, 36, 0.04), 0 1px 3px rgba(20, 24, 36, 0.06)',
        lift: '0 8px 24px -8px rgba(20, 24, 36, 0.18)',
      },
    },
  },
  plugins: [],
}
