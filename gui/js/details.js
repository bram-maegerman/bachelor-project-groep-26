const params = new URLSearchParams(window.location.search);
const filename = params.get("file");
const path = params.get("path");

const container = document.getElementById("file-details");

function extractStats(log) {
  const missingPages = log.match(/Missing pages?: (.*)/);
  const totalPages = log.match(/Total pages in document (\d+)/);
  const totalWithNumbers = log.match(/Total pages with numbers (\d+)/);
  const totalMissingPages = log.match(/Total pages with missing numbers (\d+)/);

  return {
    missing: missingPages ? missingPages[1] : "",
    total: totalPages ? totalPages[1] : "",
    withNumbers: totalWithNumbers ? totalWithNumbers[1] : "",
    withMissing: totalMissingPages ? totalMissingPages[1] : "",
  };
}

function classifyLogLine(line) {
  if (line.startsWith("[WARNING]")) return "warning";
  if (line.startsWith("[INFO]")) return "info";
  if (line.startsWith("[SUCCESS]")) return "success";
  return "log";
}

window.addEventListener("pywebviewready", async () => {
  if (!filename || !path) {
    container.innerHTML = "<p>Geen bestand opgegeven.</p>";
    return;
  }

  const title = document.createElement("h2");
  title.textContent = filename;
  container.appendChild(title);

  const file = await window.pywebview.api.get_log(path);
  const lines = file.split(/\r?\n/);
  const stats = extractStats(file);

  const statsBox = document.createElement("div");
  statsBox.classList.add("stats-box");
  statsBox.innerHTML = `
    <p><strong>Missing page numbers:</strong><br>${stats.missing}</p>
    <p><strong>Total pages:</strong><br>${stats.total}</p>
    <p><strong>Total pages with numbers:</strong><br>${stats.withNumbers}</p>
    <p><strong>Total pages with missing numbers:</strong><br>${stats.withMissing}</p>
  `;
  container.appendChild(statsBox);

  const logBox = document.createElement("div");
  logBox.classList.add("log-box");

  lines.forEach((line) => {
    if (/^(Missing pages?:|Total pages)/.test(line)) return;

    const match = line.match(/^\((\d+)\)(.*)$/);
    let pageNumber = null;
    let displayText = line;

    if (match) {
      pageNumber = parseInt(match[1], 10);
      displayText = match[2].trim();
    }

    const p = document.createElement("p");
    p.textContent = displayText;
    p.classList.add("log-line", classifyLogLine(displayText));

    if (pageNumber !== null) {
      p.style.cursor = "pointer";
      p.addEventListener("click", () => {
        const inputPage = document.getElementById("current-page");
        inputPage.value = pageNumber;
        inputPage.dispatchEvent(new Event("change"));
      });
    }

    logBox.appendChild(p);
  });


  container.appendChild(logBox);
  await loadPdf('files/'+filename)
});

async function loadPdf(path) {
  const loadingDiv = document.getElementById("pdf-loading");
  const previewDiv = document.getElementById("pdf-preview");
  const pageControl = document.getElementById("page-control");
  pageControl.style.display = "none";

  const progressText = document.createElement("p");
  progressText.innerHTML = "Getting your PDF...";

  loadingDiv.style.display = "block";
  previewDiv.innerHTML = "";
  loadingDiv.appendChild(progressText);

  const dataUrl = await window.pywebview.api.read_pdf_as_data_url(path);
  if (!dataUrl) {
    console.error("Could not read PDF as data URL:", path);
    loadingDiv.textContent = "Failed to load PDF.";
    return;
  }

  const pdf = await pdfjsLib.getDocument(dataUrl).promise;
  const totalPages = pdf.numPages;

  document.getElementById("total-pages").textContent = totalPages;

  const canvasElements = [];
  progressText.innerHTML = "";

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const percent = ((pageNum - 1) / totalPages) * 100;
    progressText.textContent = `Loading... ${percent.toFixed(0)}%`;

    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.2 });

    const canvas = document.createElement("canvas");
    canvas.setAttribute("data-page", pageNum);
    canvas.style.display = "block";
    canvas.style.marginBottom = "20px";

    const context = canvas.getContext("2d");
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport,
    };

    await page.render(renderContext).promise;
    previewDiv.appendChild(canvas);
    canvasElements.push(canvas);
  }

  loadingDiv.style.display = "none";
  pageControl.style.display = "";

  const inputPage = document.getElementById("current-page");

  inputPage.addEventListener("change", () => {
    let pageNum = parseInt(inputPage.value);
    if (isNaN(pageNum) || pageNum < 1) pageNum = 1;
    if (pageNum > totalPages) pageNum = totalPages;

    const canvas = previewDiv.querySelector(`canvas[data-page="${pageNum}"]`);
    if (canvas) {
      canvas.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const page = entry.target.getAttribute("data-page");
        inputPage.value = page;
      }
    });
  }, {
    root: previewDiv,
    threshold: 0.6
  });

  canvasElements.forEach(canvas => observer.observe(canvas));
}

