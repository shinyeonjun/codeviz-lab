/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* === 사이드바 === */
        sidebar: {
          DEFAULT: '#111318',
          light: '#1A1C23',
          muted: '#6B7280',
        },
        /* === 서페이스 === */
        surface: {
          DEFAULT: '#FFFFFF',
          soft: '#F9FAFB',
          muted: '#F3F4F6',
          border: '#E5E7EB',
        },
        /* === 단색 액센트 (단일 블루) === */
        accent: {
          DEFAULT: '#2563EB',
          light: '#DBEAFE',
        },
        /* === 텍스트 === */
        ink: {
          DEFAULT: '#111827',
          secondary: '#6B7280',
          muted: '#9CA3AF',
          faint: '#D1D5DB',
        },
      },
      boxShadow: {
        'sm': '0 1px 2px rgba(0,0,0,0.04)',
        'card': '0 1px 3px rgba(0,0,0,0.06)',
      },
      fontFamily: {
        sans: ['"Pretendard"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
