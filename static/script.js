// Core functionality is server-rendered so the app works even if JavaScript is unavailable.
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  if (form) form.addEventListener("submit", () => form.querySelector("button[type='submit']")?.setAttribute("disabled", "disabled"));
});
