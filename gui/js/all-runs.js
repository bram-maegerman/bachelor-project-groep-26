let currentPage = 1;
let allFiles = [];
let allFilteredFiles = [];
let totalPages = 1;

let ascNameSorting = true;

async function renderOverview(files) {
  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  allFiles = [];
  Object.keys(files).forEach((date) => {
    const splitDate = date.split("\\").at(-1);
    const splitDatee = splitDate.split("_").at(-1);
    const project = splitDate.split("_").at(0);

    files[date].forEach((file) => {
      allFiles.push({
        file: file,
        fileName: file.split("\\").at(-1),
        date: splitDatee,
        project: project
      });
    });
  });

  allFilteredFiles = allFiles;
  totalPages = Math.ceil(allFiles.length / 10);
  await renderPage(currentPage);
}

async function sortAllFilesByName() {
  if (ascNameSorting) {
    allFilteredFiles.sort((a, b) => b.fileName.localeCompare(a.fileName));
  } else {
    allFilteredFiles.sort((a, b) => a.fileName.localeCompare(b.fileName));
  }
  await renderPage(currentPage);
}

async function filterAllFilesByName(filterValue) {
  if (filterValue.length === 0) {
    allFilteredFiles = allFiles;
  } else {
    allFilteredFiles = allFiles.filter(file => 
      file.fileName.toLowerCase().includes(filterValue.toLowerCase())
    );
  }
  await renderPage(currentPage);
}

async function renderPage(page) {
  currentPage = page;
  const start = (page - 1) * 10;
  const end = start + 10;
  const pageFiles = allFilteredFiles.slice(start, end);

  const table = document.createElement("table");
  table.className = "file-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const nameHeader = document.createElement("th");
  nameHeader.textContent = `Name ${ascNameSorting ? '▲' : '▼'}`;
  nameHeader.className = "sortable-header"
  nameHeader.addEventListener("click", () => {
    ascNameSorting = !ascNameSorting;
    sortAllFilesByName();
  });
  headerRow.appendChild(nameHeader);

  ["Errors", "Checked", "Date", "Project"].forEach((headerText) => {
    const th = document.createElement("th");
    th.textContent = headerText;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");

  for (const fileData of pageFiles) {
    let errorCount = 0;
    let log = null;
    try {
      log = await window.pywebview.api.get_log(fileData.file);
      errorCount = parseErrorCount(log);
    } catch (error) {
      console.error("Error loading log:", error);
    }

    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    nameCell.textContent = fileData.fileName;

    const foutenCell = document.createElement("td");
    foutenCell.textContent = errorCount;

    const statusCell = document.createElement("td");
    const statusIndicator = document.createElement("div");
    statusIndicator.className = `status-circle ${
      log && parseManuallyChecked(log) ? "green" : "red"
    }`;
    statusCell.appendChild(statusIndicator);

    const datumCell = document.createElement("td");
    datumCell.textContent = fileData.date;

    const projectCell = document.createElement("td");
    projectCell.textContent = fileData.project;

    row.classList.add("clickable-row");
    row.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(
        fileData.fileName
      )}&path=${encodeURIComponent(fileData.file)}`;
    });

    row.appendChild(nameCell);
    row.appendChild(foutenCell);
    row.appendChild(statusCell);
    row.appendChild(datumCell);
    row.appendChild(projectCell);
    tbody.appendChild(row);
  }

  table.appendChild(tbody);

  const container = document.getElementById("file-list-container");
  container.innerHTML = "";
  container.appendChild(table);

  createPagination();
}

function createPagination() {
  const pagination = document.getElementById("pagination");
  pagination.innerHTML = "";

  const paginationContainer = document.createElement("div");
  paginationContainer.className = "pagination-container";

  const prevButton = document.createElement("button");
  prevButton.className = "pagination-button";
  prevButton.textContent = "◄";
  prevButton.disabled = currentPage === 1;
  prevButton.addEventListener("click", () => {
    if (currentPage > 1) renderPage(currentPage - 1);
  });

  const pageNumbers = document.createElement("div");

  for (let i = 1; i <= totalPages; i++) {
    const pageButton = document.createElement("button");
    pageButton.className = `pagination-button ${
      i === currentPage ? "active" : ""
    }`;
    pageButton.textContent = i;
    pageButton.addEventListener("click", () => renderPage(i));
    pageNumbers.appendChild(pageButton);
  }

  const nextButton = document.createElement("button");
  nextButton.className = "pagination-button";
  nextButton.textContent = "►";
  nextButton.disabled = currentPage === totalPages;
  nextButton.addEventListener("click", () => {
    if (currentPage < totalPages) renderPage(currentPage + 1);
  });

  paginationContainer.appendChild(prevButton);
  paginationContainer.appendChild(pageNumbers);
  paginationContainer.appendChild(nextButton);
  pagination.appendChild(paginationContainer);
}

function parseErrorCount(log) {
  const regex = /Total pages with missing numbers.*?(\d+)/;
  const match = log.match(regex);

  const count = match ? parseInt(match[1], 10) : 0;

  if (isNaN(count)) {
    return 0;
  }

  return count;
}

function parseManuallyChecked(log) {
  const lines = log.split("\n").filter((line) => line.trim());
  const checkedLine = lines[lines.length - 3];
  return checkedLine.split("=")[1] === "true";
}

const nameFilterInput = document.getElementById("name-filter");
nameFilterInput.addEventListener("input", () => {
  filterAllFilesByName(nameFilterInput.value.trim());
})

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_overview();
  });
});
