import { Config } from 'tailwindcss'
import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'

const config: Config = {
  // Enable dark mode via a .dark class on <html>
  darkMode: 'class',

  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}'
  ],

  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1rem', md: '2rem' },
    },

    extend: {
      colors: {
        primary: '#1BE8A5',
        secondary: '#002C3A',
        accent: {
          DEFAULT: '#FACC15',
          light: '#FDE68A',
          dark: '#CA8A04',
        },
      },
      fontFamily: {
        sans: ['Segoe UI', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      borderRadius: {
        xl: '1rem',
      },
      boxShadow: {
        glow: '0 0 10px rgba(27, 232, 165, 0.6)',
      },
      screens: {
        '3xl': '1920px',
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            a: {
              color: theme('colors.primary'),
              '&:hover': {
                color: theme('colors.accent.DEFAULT'),
              },
            },
          },
        },
        dark: {
          css: {
            color: theme('colors.gray.300'),
            a: {
              color: theme('colors.primary'),
              '&:hover': {
                color: theme('colors.accent.light'),
              },
            },
            h1: { color: theme('colors.gray.100') },
            h2: { color: theme('colors.gray.100') },
            blockquote: {
              borderLeftColor: theme('colors.secondary'),
            },
          },
        },
      }),
    },
  },

  plugins: [
    forms,
    typography,
  ],
}

export default config
