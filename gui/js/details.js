const params = new URLSearchParams(window.location.search);
const filename = params.get("file");
const path = params.get("path");

const container = document.getElementById("file-details");

function extractStats(log) {
  let [missing, total, withNumbers, withMissing] = log.split(/\r?\n/);

  return {
    missing: missing.match(/Missing pages?: (.*)/)?.[1] || "0",
    total: total.match(/Total pages in document (\d+)/)?.[1] || "0",
    withNumbers:
      withNumbers.match(/Total pages with numbers (\d+)/)?.[1] || "0",
    withMissing:
      withMissing.match(/Total pages with missing numbers (\d+)/)?.[1] || "0",
  };
}

function classifyLogLine(line) {
  if (line.startsWith("[WARNING]")) return "warning";
  if (line.startsWith("[INFO]")) return "info";
  if (line.startsWith("[SUCCESS]")) return "success";
  return "log";
}

function createStatsBox(stats) {
  const statsBox = document.createElement("div");
  statsBox.innerHTML = `
    <p><strong>Missing page numbers:</strong><br>${stats.missing}</p>
    <p><strong>Total pages:</strong><br>${stats.total}</p>
    <p><strong>Total pages with numbers:</strong><br>${stats.withNumbers}</p>
    <p><strong>Total pages with missing numbers:</strong><br>${stats.withMissing}</p>
  `;
  return statsBox;
}

function createLogBox(logText) {
  const logBox = document.createElement("div");
  logBox.className = "log-box";

  const lines = logText.split(/\r?\n/);
  for (const line of lines) {
    if (/^(Missing pages?:|Total pages)/.test(line)) continue;

    const match = line.match(/^\((\d+)\)(.*)$/);
    const pageNumber = match ? parseInt(match[1], 10) : null;
    const displayText = match ? match[2].trim() : line;

    const p = document.createElement("p");
    p.textContent = displayText;
    p.className = `log-line ${classifyLogLine(displayText)}`;

    if (pageNumber !== null) {
      p.style.cursor = "pointer";
      p.addEventListener("click", () => {
        const input = document.getElementById("current-page");
        input.value = pageNumber;
        input.dispatchEvent(new Event("change"));
      });
    }

    logBox.appendChild(p);
  }

  return logBox;
}

async function loadPdf(path) {
  const loading = document.getElementById("pdf-loading");
  const preview = document.getElementById("pdf-preview");
  const pageControl = document.getElementById("page-control");
  const pageInput = document.getElementById("current-page");

  loading.style.display = "block";
  preview.innerHTML = "";
  pageControl.style.display = "none";

  const status = document.createElement("p");
  status.textContent = "Getting your PDF...";
  loading.appendChild(status);

  const dataUrl = await window.pywebview.api.read_pdf_as_data_url(path);
  if (!dataUrl) {
    console.error("Failed to load PDF:", path);
    loading.textContent = "Failed to load PDF.";
    return;
  }

  const pdf = await pdfjsLib.getDocument(dataUrl).promise;
  const totalPages = pdf.numPages;
  document.getElementById("total-pages").textContent = totalPages;
  status.textContent = "";

  const canvases = [];

  for (let i = 1; i <= totalPages; i++) {
    status.textContent = `Loading... ${((100 * (i - 1)) / totalPages).toFixed(
      0
    )}%`;

    const page = await pdf.getPage(i);
    const viewport = page.getViewport({ scale: 1.2 });

    const canvas = document.createElement("canvas");
    canvas.dataset.page = i;
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    canvas.style.display = "block";
    canvas.style.marginBottom = "20px";

    await page.render({ canvasContext: canvas.getContext("2d"), viewport })
      .promise;

    preview.appendChild(canvas);
    canvases.push(canvas);
  }

  loading.style.display = "none";
  pageControl.style.display = "block";

  pageInput.addEventListener("change", () => {
    let pageNum = parseInt(pageInput.value);
    if (isNaN(pageNum) || pageNum < 1) pageNum = 1;
    if (pageNum > totalPages) pageNum = totalPages;

    const canvas = preview.querySelector(`canvas[data-page="${pageNum}"]`);
    canvas?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          pageInput.value = entry.target.dataset.page;
        }
      }
    },
    {
      root: preview,
      threshold: 0.6,
    }
  );

  canvases.forEach((canvas) => observer.observe(canvas));
}

window.addEventListener("pywebviewready", async () => {
  if (!filename || !path) {
    container.innerHTML = "<p>Geen bestand opgegeven.</p>";
    return;
  }

  container.appendChild(
    Object.assign(document.createElement("h2"), { textContent: filename })
  );

  const file = await window.pywebview.api.get_log(path);
  const [logText, statistics, rawPdfPath] = file.split(/\r?\n\r?\n/);

  const stats = extractStats(statistics.trim().trim("\n"));
  container.appendChild(createStatsBox(stats));
  container.appendChild(createLogBox(logText));

  const pdfPath = rawPdfPath.replace("Path to original pdf: \n", "").trim();
  console.log("PDF Path:", pdfPath);
  await loadPdf(pdfPath);
});
