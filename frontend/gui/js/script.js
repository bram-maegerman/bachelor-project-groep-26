const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("fileElem");
const fileList = document.getElementById("file-list");

let currentFiles = [];

dropArea.addEventListener("click", () => fileInput.click());

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.add("dragover"),
    false
  );
});

["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.remove("dragover"),
    false
  );
});

dropArea.addEventListener("drop", handleDrop, false);
fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
});

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  addFiles(files);
}

function addFiles(files) {
  for (const file of files) {
    if (file.type !== "application/pdf") {
      alert(`"${file.name}" is geen PDF-bestand en wordt overgeslagen.`);
      continue;
    }

    const alreadyAdded = currentFiles.some(
      (f) => f.name === file.name && f.size === file.size
    );
    if (!alreadyAdded) {
      currentFiles.push(file);
    }
  }
  updateFileList();
}

function updateFileList() {
  const fileSection = document.getElementById("file-section");
  fileSection.innerHTML = "";

  if (currentFiles.length === 0) {
    fileSection.textContent = "Geen bestanden geselecteerd.";
    return;
  }

  const container = document.createElement("div");
  container.className = "container";

  const listWrapper = document.createElement("div");
  listWrapper.className = "list-wrapper";

  const title = document.createElement("h3");
  title.textContent = "Geselecteerde bestanden";
  listWrapper.appendChild(title);

  const ul = document.createElement("ul");

  currentFiles.forEach((file, index) => {
    const li = document.createElement("li");
    li.textContent = `${file.name} (${formatFileSize(file.size)}) `;

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.textContent = "×";
    removeBtn.title = "Verwijderen";

    removeBtn.addEventListener("click", () => {
      currentFiles.splice(index, 1);
      updateFileList();
    });

    li.appendChild(removeBtn);
    ul.appendChild(li);
  });

  listWrapper.appendChild(ul);

  const checkWrapper = document.createElement("div");
  checkWrapper.className = "check-wrapper";

  const checkButton = document.createElement("button");
  checkButton.textContent = "Controleer";
  checkButton.className = "check-btn";

  checkButton.addEventListener("click", async () => {
    if (window.pywebview?.api?.greet) {
      const result = await window.pywebview.api.greet();
      console.log("Backend said:", result);
    } else {
      console.warn("PyWebView API not ready yet");
    }
  }); 
  checkWrapper.appendChild(checkButton);

  container.appendChild(listWrapper);
  container.appendChild(checkWrapper);

  fileSection.appendChild(container);
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  else return (bytes / 1048576).toFixed(1) + " MB";
}
