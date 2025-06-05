const currentFiles = [];
let exportPaths = [];
let selectedExportPath = null;

async function pickFile() {
  if (!window.pywebview?.api?.open_file_dialog) {
    alert("Backend API not available");
    return;
  }
  currentFiles.length = 0;
  const paths = await window.pywebview.api.open_file_dialog();

  currentFiles.length = 0;
  if (paths && paths.length > 0) {
    paths.forEach((path) => {
      currentFiles.push({
        name: path.split(/[/\\]/).pop(),
        path: path,
      });
    });
  } else {
  }
  updateFileList();
}

async function checkFiles() {
  if (!selectedExportPath) {
    alert("Select a project first!");
    return;
  }

  if (currentFiles.length === 0) {
    alert("Select a minimum of 1 file!");
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

function renderProjects() {
  const options = document.getElementById("project-options");
  options.innerHTML = "";

  Object.keys(exportPaths).forEach((entry) => {
    const option = document.createElement("li");
    option.textContent = entry;
    option.addEventListener("click", async () => {
      document.getElementById("project-dropdown").textContent = entry;
      document.getElementById("project-options").classList.toggle("hidden");
      projectDropDown.style.borderRadius = "25px";
      selectedExportPath = entry;
      await window.pywebview.api.set_export_path(exportPaths[entry]);
    });
    options.appendChild(option);
  });
}

window.addEventListener("pywebviewready", async () => {
  try {
    selectedExportPath = null;
    const projects = await window.pywebview.api.get_projects();
    exportPaths = projects || [];
    renderProjects();
  } catch (err) {
    console.error("Failed to initialize settings:", err);
  }
});
