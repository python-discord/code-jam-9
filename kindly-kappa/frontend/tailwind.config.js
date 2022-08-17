module.exports = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        onedarkpro: {
          ...require("daisyui/src/colors/themes")["[data-theme=dark]"],
          "base-100": "#282c34",
          primary: "#81279C",
        },
      },
      "dark",
      "emerald",
      "forest",
      "dracula",
      "night",
      "lemonade",
      "winter",
    ],
  },
};
