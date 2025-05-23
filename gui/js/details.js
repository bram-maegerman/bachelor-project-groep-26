const params = new URLSearchParams(window.location.search);
const filename = params.get("file");

const container = document.getElementById("file-details");

window.addEventListener("pywebviewready", async () => {
  if (!filename) {
    container.innerHTML = "<p>Geen bestand opgegeven.</p>";
    return;
  }

  const title = document.createElement("h2");
  title.textContent = `Details voor: ${filename}`;
  container.appendChild(title);

  const file = await window.pywebview.api.get_log(filename);
  const details = file.split(/\r?\n/); // use regex for cross-platform

  const ul = document.createElement("ul");

  details.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });

  container.appendChild(ul);
});
