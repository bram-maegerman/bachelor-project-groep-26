const fullOverview = document.getElementById("fullOverview");

function renderLastRun(files) {
  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  const ul = document.createElement("ul");
  files.forEach((file) => {
    const li = document.createElement("li");
    const cutPath = file.split("/").at(-1);
    li.textContent = cutPath;
    li.classList.add("clickable-li");
    li.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(
        cutPath
      )}&path=${encodeURIComponent(file)}`;
    });
    ul.appendChild(li);
  });
  container.appendChild(ul);
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_last();
  });

  fullOverview.addEventListener("click", () => {
    window.location.href = "alle-runs.html";
  });
});
