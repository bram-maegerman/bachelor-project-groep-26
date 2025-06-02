function renderLastRun(files) {
  const container = document.getElementById("file-list-container");
  const noFilesContainer = document.getElementById("no-files");

  const table = document.createElement("table");
  table.className = "file-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  ["Name", "Errors", "Status", "Date"].forEach((headerText) => {
    const th = document.createElement("th");
    th.textContent = headerText;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");

  if (files.length == 0) {
    const noFiles = document.createElement("p");
    noFiles.innerHTML = "No runs performed yet during this session.";
    noFilesContainer.appendChild(noFiles);
  }

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

function parseErrorCount(log) {
  const lines = log.split("\n").filter((line) => line.trim());
  const lastLine = lines[lines.length - 3];
  const parts = lastLine.split(" ");
  const count = parseInt(parts[parts.length - 1], 10);
  return count;
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_last();
  });
});
