const currentFiles = [];

async function pickFile() {
  if (!window.pywebview?.api?.open_file_dialog) {
    alert("Backend API not available");
    return;
  }
  currentFiles.length = 0;
  const paths = await window.pywebview.api.open_file_dialog();

  if (paths && paths.length > 0) {
    currentFiles.length = 0;
    paths.forEach((path) => {
      currentFiles.push({
        name: path.split(/[/\\]/).pop(),
        path: path,
      });
    });
    updateFileList();
  } else {
    currentFiles.length = 0;
    updateFileList();
  }
}

async function checkFiles() {
  if (currentFiles.length === 0) {
    alert("Select a mininum of 1 file!");
    return;
  }
  if (currentFiles.length > 20) {
    alert("Select fewer than 20 files!");
    return;
  }
  const filePaths = currentFiles.map((file) => file.path);

  await window.pywebview.api.set_next(filePaths);

  window.location.href = "progress.html";
}

function updateFileList() {
  const fileListContainer = document.getElementById("file-list");
  fileListContainer.innerHTML = "";

  if (currentFiles.length === 0) {
    fileListContainer.textContent = "";
  } else {
    const ul = document.createElement("ul");

    currentFiles.forEach((file, index) => {
      const li = document.createElement("li");
      li.textContent = file.name;

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

    fileListContainer.appendChild(ul);
  }

  const countEl = document.getElementById("file-count");
  countEl.style.color = currentFiles.length > 20 ? "red" : "white";

  countEl.textContent = `${currentFiles.length}/20`;
}
