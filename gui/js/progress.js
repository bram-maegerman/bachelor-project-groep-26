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

  const stepToRemove = document.getElementById("current-step");
  if (stepToRemove) {
    stepToRemove.remove();
  }
  
  // children[0] is the status element
  // children[1] is the file name of path
  children[0].className = inProgressClassName;
  children[0].innerHTML = "O";

  const currentStep = document.createElement("div");
  currentStep.id = "current-step";
  currentStep.className = "current-step";
  currentStep.innerHTML =  "Processing";

  const percentage = document.createElement("div");
  percentage.id = "percentage";
  percentage.innerHTML = "(0%)";
  currentStep.appendChild(percentage);
  
  children[1].appendChild(currentStep);
}

function updatePercentage(percentage_str) {
  const percentage = document.getElementById("percentage");
  percentage.innerHTML = `(${percentage_str})`;
}

function startCompressing() {
  const currentStep = document.getElementById("current-step");
  currentStep.innerHTML = "Compressing...";
}

function finished() {
  const loader = document.getElementById("loader");
  const overzicht = document.getElementById("overzicht");

  loader.className = "hidden";
  overzicht.classList.remove("hidden");

  const stepToRemove = document.getElementById("current-step");
  if (stepToRemove) {
    stepToRemove.remove();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_script_on_files();
  });
});
