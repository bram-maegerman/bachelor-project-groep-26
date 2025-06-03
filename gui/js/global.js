const ARROW_UP = "▲"; // \u25B2
const ARROW_DOWN = "▼"; // \u25BC

function toggleArrow(currentArrow) {
  return currentArrow === ARROW_UP ? ARROW_DOWN : ARROW_UP;
}

const navDropdown = document.getElementById("nav-dropdown");
const navArrow = document.getElementById("nav-arrow");
const options = document.getElementById("options");
const projectDropDown = document.getElementById("project-dropdown");
const projectOptions = document.getElementById("project-options");
const projectArrow = document.getElementById("project-arrow");

document.addEventListener("DOMContentLoaded", () => {
  if (navDropdown && navArrow && options) {
    navDropdown.addEventListener("click", () => {
      navArrow.textContent = toggleArrow(navArrow.textContent.trim());
      options.classList.toggle("hidden");
      navDropdown.style.borderRadius = options.classList.contains("hidden")
        ? "25px"
        : "25px 25px 0 0";
    });
  }
  if (projectDropDown && navArrow && options) {
    projectDropDown.addEventListener("click", () => {
      projectArrow.textContent = toggleArrow(projectArrow.textContent.trim());
      projectOptions.classList.toggle("hidden");
      projectDropDown.style.borderRadius = projectOptions.classList.contains("hidden")
        ? "25px"
        : "25px 25px 0 0";
    });
  }
});