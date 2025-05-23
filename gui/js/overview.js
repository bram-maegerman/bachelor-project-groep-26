function renderOverview(files) {
  filesList = files;
  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  const ul = document.createElement("ul");
  files.forEach((file) => {
    const li = document.createElement("li");
    li.textContent = file;
    li.classList.add("clickable-li");
    li.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(file)}`;
    });
    ul.appendChild(li);
  });

  container.appendChild(ul);
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_overview();
  });
});
