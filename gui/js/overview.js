const itemsPerPage = 10;
let currentPage = 1;
let files = [];

async function renderListPage(page) {
  window.addEventListener("pywebviewready", async () => {
    files = await window.pywebview.api.get_files();
    console.log(files);
    const container = document.getElementById("file-list-container");
    container.innerHTML = "";

    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const filesToDisplay = files.slice(start, end);

    const ul = document.createElement("ul");
    filesToDisplay.forEach((file) => {
      const li = document.createElement("li");
      li.textContent = file;
      li.classList.add("clickable-li");
      li.addEventListener("click", () => {
        window.location.href = `details.html?file=${encodeURIComponent(file)}`;
      });
      ul.appendChild(li);
    });

    container.appendChild(ul);
  });
}

function renderPagination() {
  const paginationContainer = document.getElementById("pagination");
  paginationContainer.innerHTML = "";

  const pageCount = Math.ceil(files.length / itemsPerPage);

  for (let i = 1; i <= pageCount; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    if (i === currentPage) {
      btn.classList.add("active");
    }

    btn.addEventListener("click", () => {
      currentPage = i;
      renderListPage(currentPage);
      renderPagination();
    });

    paginationContainer.appendChild(btn);
  }
}

renderListPage(currentPage);
renderPagination();
