function renderOverview(files) {
  const container = document.getElementById("file-list-container");
  container.innerHTML = "";

  
  let dates = Object.keys(files)
  dates.forEach((date) => {
    const div = document.createElement("div")
    div.className = 'date-container'
      const ul = document.createElement("ul");

      let splitDate = date.split('\\').at(-1);
      const h2 = document.createElement("h2")
      h2.innerText = splitDate
      h2.className = "date-title"
      div.appendChild(h2)
      div.appendChild(ul)
      let subFiles = files[date]
      subFiles.forEach((file) => {
        const li = document.createElement("li");
        const cutPath = file.split('/').at(-1)
        li.textContent = cutPath;
        li.classList.add("clickable-li");
        li.addEventListener("click", () => {
          window.location.href = `details.html?file=${encodeURIComponent(cutPath)}&path=${encodeURIComponent(file)}`;
        });
      
      ul.appendChild(li);
    });
    container.appendChild(div);
  })

}

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", () => {
    window.pywebview.api.run_overview();
  });
});
