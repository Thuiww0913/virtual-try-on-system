/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      screens: {
        // 4K 大屏断点（65 寸触控屏 3840×2160 会命中）
        // 默认: sm=640 md=768 lg=1024 xl=1280 2xl=1536
        '3xl': '2400px',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'Inter', 'sans-serif'],
        body: ['Inter', '"DM Sans"', 'sans-serif'],
      },
      colors: {
        ink: {
          950: '#07080b',
          900: '#0b0d12',
          800: '#12141b',
          750: '#171a22',
          700: '#1e222c',
          600: '#2a2f3c',
          500: '#3a404f',
          400: '#5a6071',
        },
        accent: {
          DEFAULT: '#c8ff3d',
          dim: '#a8e01d',
          soft: '#e8ff8a',
        },
        cyan: {
          tech: '#3dd6ff',
          glow: '#5de8ff',
        },
      },
      boxShadow: {
        'accent-glow': '0 0 40px -4px rgba(200,255,61,0.35)',
        'cyan-glow': '0 0 40px -4px rgba(61,214,255,0.35)',
        'card': '0 8px 32px -8px rgba(0,0,0,0.6)',
        'card-hover': '0 20px 60px -10px rgba(0,0,0,0.8)',
      },
      animation: {
        'fade-up': 'fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both',
        'fade-in': 'fadeIn 0.5s ease both',
        'pulse-soft': 'pulseSoft 2.5s ease-in-out infinite',
        'shimmer': 'shimmer 2.2s linear infinite',
        'scan': 'scan 2.2s linear infinite',
        'float': 'float 4s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseSoft: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0.55' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        scan: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%':     { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
}
