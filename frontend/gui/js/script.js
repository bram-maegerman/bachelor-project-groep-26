const currentFiles = [];

function pickFile() {
  if (!window.pywebview?.api?.open_file_dialog) {
    alert("Backend API not available");
    return;
  }

  window.pywebview.api.open_file_dialog().then((paths) => {
    if (paths && paths.length > 0) {
      currentFiles.length = 0; // clear previous selections

      paths.forEach((path) => {
        currentFiles.push({
          name: path.split(/[/\\]/).pop(),
          size: 0,
          path: path,
        });
      });

      document.getElementById("filePath").textContent = "";
      // "Geselecteerde bestanden:\n" +
      // currentFiles.map((f) => f.name).join("\n");

      updateFileList();
    } else {
      document.getElementById("filePath").textContent =
        "Geen bestanden geselecteerd.";
      currentFiles.length = 0;
      updateFileList();
    }
  });
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
    li.textContent = `${file.name} (${
      file.size ? formatFileSize(file.size) : "onbekend formaat"
    }) `;

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.textContent = "×";
    removeBtn.title = "Verwijderen";

    removeBtn.addEventListener("click", () => {
      currentFiles.splice(index, 1);
      updateFileList();
      document.getElementById("filePath").textContent = currentFiles.length
        ? "Geselecteerd bestand: " + currentFiles[0].path
        : "";
    });

    li.appendChild(removeBtn);
    ul.appendChild(li);
  });

  listWrapper.appendChild(ul);

  container.appendChild(listWrapper);

  fileSection.appendChild(container);
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  else return (bytes / 1048576).toFixed(1) + " MB";
}
