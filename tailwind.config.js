/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/*.html"],
  theme: {
    extend: {
      gridTemplateColumns: {
        '16': 'repeat(16, minmax(0, 1fr))',

        'footer': '200px minmax(900px, 1fr) 100px',
      }
    },
    fontFamily: {
      sans:['Graphik', 'Open Sans', 'sans-serif'],
      lato:['Lato','sans-serif']
    },
    screens: {
      sm: '480px',
      md: '768px',
      lg: '976px',
      xl: '1440px',
    },
  },
  
  plugins: [],
}

