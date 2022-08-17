import { dracula } from "./themes/dracula";
import { emerald } from "./themes/emerald";
import { greenery } from "./themes/greenery";
import { nightowl } from "./themes/nightowl";
import { onedark } from "./themes/onedark";
import { winter } from "./themes/winter";

export const themes = [
  {
    name: "onedarkpro",
    theme: onedark,
  },
  {
    name: "dracula",
    theme: dracula,
  },
  {
    name: "night",
    theme: nightowl,
  },
  {
    name: "dark",
    theme: onedark, // Use the onedarkpro for the "dark" theme too
  },
  {
    name: "emerald",
    theme: emerald,
  },
  {
    name: "forest",
    theme: greenery,
  },
  {
    name: "winter",
    theme: winter,
  },
];
