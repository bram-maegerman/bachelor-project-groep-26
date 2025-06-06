let inProgressClassName = "in-progress";
let doneClassName = "done";
let errorClassName = "error";
let queuedClassName = "queued";

const progressList = document.getElementById("progress-list");

function loadFilesInTable(files) {
  const allFilesList = document.createElement("ul");

  for (const index in files) {
    let li = document.createElement("li");
    li.id = files[index]

    let status = document.createElement("div");
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
  children = fileToUpdate.children

  if (result.success) {
    children[0].className = doneClassName;
    children[0].innerHTML = "V";
  } else {
    children[0].className = errorClassName;
    children[0].innerHTML = "X";
  }

  children[1].innerHTML = children[1].innerHTML.split(" - ")[0];
}

function setFileInProgress(file) {
  const fileToUpdate = document.getElementById(file);
  children = fileToUpdate.children

  // children[0] is the status element
  // children[1] is the file name of path
  children[0].className = inProgressClassName;
  children[0].innerHTML = "O";

  children[1].innerHTML = children[1].innerHTML.concat(" - processing");

  const percentage = document.createElement("div");
  percentage.id = "percentage";
  percentage.innerHTML = "(0%)";

  children[1].appendChild(percentage);
}

function updatePercentage(percentage_str) {
  const percentage = document.getElementById("percentage");
  percentage.innerHTML = `(${percentage_str})`;
}

function startCompressing(file) {
  const fileToUpdate = document.getElementById(file);
  children = fileToUpdate.children

  children[1].innerHTML = children[1].innerHTML.replace("processing", "compressing");
  children[1].removeChild(document.getElementById("percentage"));
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
