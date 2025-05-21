const params = new URLSearchParams(window.location.search);
const filename = params.get("file");

const container = document.getElementById("file-details");

const detailsData = [
  "Er mist een pagina met 45",
  "Pagina 1-10 hebben geen paginanummer",
];

if (filename) {
  const title = document.createElement("h2");
  title.textContent = `Details voor: ${filename}`;
  container.appendChild(title);

  const ul = document.createElement("ul");

  detailsData.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });

  container.appendChild(ul);
} else {
  container.innerHTML = "<p>Geen bestand opgegeven.</p>";
}
