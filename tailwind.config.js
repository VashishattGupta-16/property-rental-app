/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./rental_app/templates/**/*.html",
    "./tweet/templates/**/*.html",
    "./**/*.py",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      boxShadow: {
        pro: "0 30px 80px rgba(0,0,0,0.35)",
      },
      fontFamily: {
        sans: ["\"Plus Jakarta Sans\"", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
