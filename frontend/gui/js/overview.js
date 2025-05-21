const files = Array.from({ length: 73 }, (_, i) => ({
  name: `file_${i + 1}.txt`,
  link: `#file_${i + 1}`,
}));

const itemsPerPage = 10;
let currentPage = 1;

function renderListPage(page) {
  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const filesToDisplay = files.slice(start, end);

  const ul = document.createElement("ul");
  filesToDisplay.forEach((file) => {
    const li = document.createElement("li");
    li.textContent = file.name;
    li.classList.add("clickable-li");
    li.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(
        file.name
      )}`;
    });
    ul.appendChild(li);
  });

  container.appendChild(ul);
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
