

function loadFilesInTable(files) {
    console.log(files)
}

function updateResults(results) {
  console.log(results)
}

document.addEventListener("DOMContentLoaded", function () {
    if (window.pywebview) {
        window.pywebview.api.page_loaded().then()
    }
});