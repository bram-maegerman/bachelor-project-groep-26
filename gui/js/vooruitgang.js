let inProgressClassName = "in-progress";
let doneClassName = "done";
let errorClassName = "error";
let queuedClassName = "queued";

const progressList = document.getElementById("progress-list");

function loadFilesInTable(files) {
  const allFilesList = document.createElement("ul");

  for (const index in files) {
    let li = document.createElement("li");

    let status = document.createElement("div");
    status.id = files[index];
    status.className = queuedClassName;
    status.innerHTML = "-";
    li.appendChild(status);

    const p = document.createElement("p");
    p.innerHTML = files[index];
    li.appendChild(p);

    allFilesList.appendChild(li);
  }

  progressList.appendChild(allFilesList);
}

function updateResult(result) {
  const fileToUpdate = document.getElementById(result.file);

  if (result.success) {
    fileToUpdate.className = doneClassName;
    fileToUpdate.innerHTML = "V";
  } else {
    fileToUpdate.className = errorClassName;
    fileToUpdate.innerHTML = "X";
  }
}

function setFileInProgress(file) {
  const fileToUpdate = document.getElementById(file);
  fileToUpdate.className = inProgressClassName;
  fileToUpdate.innerHTML = "O";
}

function finished() {
  const loader = document.getElementById("loader");
  const overzicht = document.getElementById("overzicht");

  loader.className = "hidden";
  overzicht.classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_script_on_files();
  });
});
