let currentPage = 1;
let allFiles = [];
let totalPages = 1;

async function renderOverview(files) {
  const container = document.getElementById("file-list-container");
  container.innerHTML = "<h1 class='title'>Alle runs</h1>";

  // Flatten all files into a single array
  allFiles = [];
  Object.keys(files).forEach(date => {
    const splitDate = date.split('\\').at(-1);
    
    files[date].forEach(file => {
      allFiles.push({
        file: file,
        fileName: file.split('/').at(-1),
        date: splitDate
      });
    });
  });

  totalPages = Math.ceil(allFiles.length / 10);
  await renderPage(currentPage);
}

async function renderPage(page) {
  currentPage = page;
  const start = (page - 1) * 10;
  const end = start + 10;
  const pageFiles = allFiles.slice(start, end);

  const container = document.getElementById("file-list-container");
  container.innerHTML = "<h1 class='title'>Alle runs</h1>";

  // Create table structure
  const table = document.createElement("table");
  table.className = "file-table";
  
  // Table headers
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  ["Name", "Fouten", "Status", "Datum"].forEach(headerText => {
    const th = document.createElement("th");
    th.textContent = headerText;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Table body
  const tbody = document.createElement("tbody");
  
  for (const fileData of pageFiles) {
    let errorCount = 0;
    try {
      const log = await window.pywebview.api.get_log(fileData.file);
      errorCount = parseErrorCount(log);
    } catch (error) {
      console.error('Error loading log:', error);
    }

    const row = document.createElement("tr");
    
    // Name column
    const nameCell = document.createElement("td");
    nameCell.textContent = fileData.fileName;
    
    // Fouten column
    const foutenCell = document.createElement("td");
    foutenCell.textContent = errorCount;
    
    // Status column
    const statusCell = document.createElement("td");
    const statusIndicator = document.createElement("div");
    statusIndicator.className = `status-circle ${errorCount > 0 ? 'red' : 'green'}`;
    statusCell.appendChild(statusIndicator);
    
    // Datum column
    const datumCell = document.createElement("td");
    datumCell.textContent = fileData.date;
    
    // Click handler
    row.classList.add("clickable-row");
    row.addEventListener("click", () => {
      window.location.href = `details.html?file=${encodeURIComponent(fileData.fileName)}&path=${encodeURIComponent(fileData.file)}`;
    });

    row.appendChild(nameCell);
    row.appendChild(foutenCell);
    row.appendChild(statusCell);
    row.appendChild(datumCell);
    tbody.appendChild(row);
  }

  table.appendChild(tbody);
  container.appendChild(table);
  createPagination();
}

function createPagination() {
  const pagination = document.getElementById("pagination");
  pagination.innerHTML = '';

  const paginationContainer = document.createElement("div");
  paginationContainer.className = "pagination-container";

  // Previous button
  const prevButton = document.createElement("button");
  prevButton.className = "pagination-button";
  prevButton.textContent = "◄";
  prevButton.disabled = currentPage === 1;
  prevButton.addEventListener("click", () => {
    if (currentPage > 1) renderPage(currentPage - 1);
  });

  // Page numbers
  const pageNumbers = document.createElement("div");
  pageNumbers.className = "page-numbers";
  
  for (let i = 1; i <= totalPages; i++) {
    const pageButton = document.createElement("button");
    pageButton.className = `pagination-button ${i === currentPage ? 'active' : ''}`;
    pageButton.textContent = i;
    pageButton.addEventListener("click", () => renderPage(i));
    pageNumbers.appendChild(pageButton);
  }

  // Next button
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
  const lines = log.split('\n').filter(line => line.trim());
  
  const lastLine = lines[lines.length - 1];
  const parts = lastLine.split(' ');
  const count = parseInt(parts[parts.length - 1], 10);
  
  return count;
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_overview();
  });
});
