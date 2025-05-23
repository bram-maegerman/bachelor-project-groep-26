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

async function checkFiles() {
  if (currentFiles.length === 0) {
    alert("Selecteer minimum 1 bestand!");
  }
  const filePaths = currentFiles.map((file) => file.path);

  const result = await window.pywebview.api.run_script_on_files(filePaths);

  const outputPaths = result.map((item) => item.stdout);

  console.log(outputPaths);
  window.location.href = "overview.html";
}

function updateFileList() {
  const fileSection = document.getElementById("file-section");
  fileSection.innerHTML = "";

  if (currentFiles.length === 0) {
    fileSection.textContent = "Geen bestanden geselecteerd.";
    return;
  }

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
  fileSection.appendChild(listWrapper);
}
