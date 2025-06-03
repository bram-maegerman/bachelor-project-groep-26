let ascNameSorting = true;
let allFiles = [];
let allFilteredFiles = [];

function parseErrorCount(log) {
  const lines = log.split("\n").filter((line) => line.trim());
  const lastLine = lines[lines.length - 3];
  const parts = lastLine.split(" ");
  const count = parseInt(parts[parts.length - 1], 10);
  return count;
}

function filterFilesByName(filterValue) {
  if (filterValue.length === 0) {
    allFilteredFiles = allFiles;
  } else {
    allFilteredFiles = allFiles.filter((file) =>
      file.toLowerCase().includes(filterValue.toLowerCase())
    );
  }
  renderProjectOverview(allFilteredFiles);
}

const nameFilterInput = document.getElementById("name-filter");
nameFilterInput.addEventListener("input", () => {
  filterFilesByName(nameFilterInput.value.trim());
});

function sortFilesByName(files) {
  if (ascNameSorting) {
    files.sort((a, b) => b.localeCompare(a));
  } else {
    files.sort((a, b) => a.localeCompare(b));
  }
  renderProjectOverview(files);
}

function renderProjectOverview(files) {
  const noFilesContainer = document.getElementById("no-files");
  if (files.length === 0) {
    noFilesContainer.style.display = "block";
    return;
  } else {
    noFilesContainer.style.display = "none";
  }

  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  const table = document.createElement("table");
  table.className = "file-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const nameHeader = document.createElement("th");
  nameHeader.textContent = `Name ${ascNameSorting ? "▲" : "▼"}`;
  nameHeader.className = "sortable-header";
  nameHeader.addEventListener("click", () => {
    ascNameSorting = !ascNameSorting;
    sortFilesByName(files);
  });
  headerRow.appendChild(nameHeader);

  ["Errors", "Status", "Date"].forEach((headerText) => {
    const th = document.createElement("th");
    th.textContent = headerText;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");

  files.forEach(async (file) => {
    const row = document.createElement("tr");

    const fileName = file.split("/").at(-1);
    const date = file.split("\\").at(-2) || "";

    let errorCount = 0;
    try {
      const log = await window.pywebview.api.get_log(file);
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
      errorCount > 0 ? "red" : "green"
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
  container.appendChild(table);
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", async () => {
    const backButton = document.getElementById("back-button");
    const removeButton = document.getElementById("remove-button");

    backButton.addEventListener("click", () => {
      window.history.back();
    });

    removeButton.addEventListener("click", async () => {
      const params = new URLSearchParams(window.location.search);
      const filename = params.get("project");

      if (!filename) {
        console.error("No project specified in URL parameters.");
        return;
      }

      if (
        !confirm(
          "Are you sure you want to remove this project? This action cannot be undone."
        )
      ) {
        return;
      }

      const projectName = decodeURIComponent(filename);
      await window.pywebview.api.remove_project(projectName);
      window.location.href = "projects.html";
    });

    const title = document.getElementById("title");

    const params = new URLSearchParams(window.location.search);
    const filename = params.get("project");

    if (!filename) {
      console.error("No project specified in URL parameters.");
      return;
    }

    const projectName = decodeURIComponent(filename);

    title.textContent = `Project: ${projectName}`;

    await window.pywebview.api.project_overview(projectName);
  });
});
