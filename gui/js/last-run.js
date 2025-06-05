let allFiles = [];
let allFilteredFiles = [];
let ascNameSorting = true;

function sortFilesByName(files) {
  if (ascNameSorting) {
    files.sort((a, b) => b.localeCompare(a));
  } else {
    files.sort((a, b) => a.localeCompare(b));
  }
  renderLastRun(files);
}

function filterFilesByName(filterValue) {
  if (filterValue.length === 0) {
    allFilteredFiles = allFiles;
  } else {
    allFilteredFiles = allFiles.filter(file => 
      file.toLowerCase().includes(filterValue.toLowerCase())
    );
  }
  renderLastRun(allFilteredFiles);
}

function renderLastRun(files) {
  const table = document.createElement("table");
  table.className = "file-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const nameHeader = document.createElement("th");
  nameHeader.textContent = `Name ${ascNameSorting ? '▲' : '▼'}`;
  nameHeader.className = "sortable-header"
  nameHeader.addEventListener("click", () => {
    ascNameSorting = !ascNameSorting;
    sortFilesByName(files);
  });
  headerRow.appendChild(nameHeader);

  ["Errors", "Checked", "Date"].forEach((headerText) => {
    const th = document.createElement("th");
    th.textContent = headerText;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");

  const noFilesContainer = document.getElementById("no-files");
  noFilesContainer.innerHTML = "";

  if (allFiles.length == 0) {
    const noFiles = document.createElement("p");
    noFiles.innerHTML = "No runs performed yet during this session.";
    noFilesContainer.appendChild(noFiles);
  }

  files.forEach(async (file) => {
    const row = document.createElement("tr");

    const fileName = file.split("/").at(-1);
    const date = file.split(/[/\\]/).at(-2) || "";

    let errorCount = 0;
    let log = null;
    try {
      log = await window.pywebview.api.get_log(file);
      errorCount = parseErrorCount(log);
    } catch (error) {
      console.error("Error loading log:", error);
    }

    const nameCell = document.createElement("td");
    nameCell.textContent = fileName;

    const foutenCell = document.createElement("td");
    foutenCell.textContent = errorCount;

    const statusCell = document.createElement("td");
    const statusIndicator = document.createElement("div");
    statusIndicator.className = `status-circle ${
      log && parseManuallyChecked(log) ? "green" : "red"
    }`;
    statusCell.appendChild(statusIndicator);

    const datumCell = document.createElement("td");
    datumCell.textContent = date;

    row.classList.add("clickable-row");
    row.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(
        fileName
      )}&path=${encodeURIComponent(file)}`;
    });

    row.appendChild(nameCell);
    row.appendChild(foutenCell);
    row.appendChild(statusCell);
    row.appendChild(datumCell);
    tbody.appendChild(row);
  });

  table.appendChild(tbody);

  const container = document.getElementById("file-list-container");
  container.innerHTML = "";
  container.appendChild(table);
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
  const checkedLine = lines[lines.length - 5];
  return checkedLine.split("=")[1] === "true";
}

const nameFilterInput = document.getElementById("name-filter");
nameFilterInput.addEventListener("input", () => {
  filterFilesByName(nameFilterInput.value.trim());
})

function loadLastRunFiles(lastRunFiles) {
  allFiles = lastRunFiles;
  renderLastRun(allFiles);
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_last();
  });
});
