const currentFiles = [];

function pickFile() {
  if (!window.pywebview?.api?.open_file_dialog) {
    alert("Backend API not available");
    return;
  }

  window.pywebview.api.open_file_dialog().then((paths) => {
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
  });
}

function updateFileList() {
  const fileSection = document.getElementById("file-section");
  const buttonSection = document.getElementById("button-section")
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

  listWrapper.appendChild(ul);

  container.appendChild(listWrapper);

  const checkWrapper = document.createElement("div");
  checkWrapper.className = "check-wrapper";

  const checkBtn = document.createElement("button");
  checkBtn.className = "standard-btn";
  checkBtn.textContent = "Controleer";
  checkBtn.title = "Controleren";

  checkBtn.addEventListener("click", () => {
    const filePaths = currentFiles.map((file) => file.path);

    window.pywebview.api.run_script_on_files(filePaths).then(function (output) {
      console.log(output);
    });
    console.log(filePaths);
  });

  checkWrapper.appendChild(checkBtn);
  container.appendChild(checkWrapper);
  fileSection.appendChild(container);

  fileSection.appendChild(container);
}
