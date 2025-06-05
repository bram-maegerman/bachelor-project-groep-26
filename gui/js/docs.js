window.addEventListener("scroll", () => {
  const sections = document.querySelectorAll("section[id]");
  const links = document.querySelectorAll(".content-table a");

  let currentId = "";

  sections.forEach((section) => {
    const rect = section.getBoundingClientRect();
    if (rect.top <= 100 && rect.bottom >= 100) {
      currentId = section.id;
    }
  });

  links.forEach((link) => {
    link.classList.toggle(
      "active",
      link.getAttribute("href") === `#${currentId}`
    );
  });
});
