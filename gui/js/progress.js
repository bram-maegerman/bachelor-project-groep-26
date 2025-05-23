allFiles = []

inProgressClassName = "status in-progress"
doneClassName = "status done"
errorClassName = "status error"
queuedClassName = "status queued"

function loadFilesInTable(files) {
    const progressList = document.getElementById("progress-list");

    const allFilesList = document.createElement("ul");

    for(const index in files){
        let li = document.createElement("li");
        li.innerHTML = files[index];
        
        let status = document.createElement("div");
        status.id = files[index];
        status.className = queuedClassName;
        status.innerHTML = "-";
        li.appendChild(status);
        allFilesList.appendChild(li);
    }

    progressList.appendChild(allFilesList);
}

function updateResult(result) {
    const fileToUpdate = document.getElementById(result.file);

    if(result.success){
        fileToUpdate.className = doneClassName;
        fileToUpdate.innerHTML = "V";
    } else {
        fileToUpdate.className = errorClassName;
        fileToUpdate.innerHTML = "X";
    }
}

function setFileInProgress(file) {
    console.log(file)
    const fileToUpdate = document.getElementById(file);
    fileToUpdate.className = inProgressClassName;
    fileToUpdate.innerHTML = "O";
}

document.addEventListener("DOMContentLoaded", () => {
    window.addEventListener("pywebviewready", () => {
        window.pywebview.api.page_loaded()
    });
});