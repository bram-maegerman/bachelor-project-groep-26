document.addEventListener("DOMContentLoaded", () => {
  ///////////////////////////////////////////////
  ////     G L O B A L   V A R I A B L E S   ////
  ///////////////////////////////////////////////

  let logLevel = 2;
  let exportPaths = [];
  let projectNameToAdd = '';

  const logOptions = {
    1: { id: "log-level-1", description: "Only warnings are shown" },
    2: { id: "log-level-2", description: "Warnings and info messages are shown" },
    3: { id: "log-level-3", description: "All logs are shown" },
  };

  /////////////////////////////////////
  ////     E L E M E N T S   //////////
  /////////////////////////////////////

  const saveButton = document.getElementById("save-button");
  const resetButton = document.getElementById("reset-button");
  const exportList = document.getElementById("export-paths-list");
  const addPathButton = document.getElementById("choose-new-export-folder");
  const exportName = document.getElementById("new-export-name");
  const descriptionElement = document.getElementById("log-level-description");
  const option1 = document.getElementById("log-level-1");
  const option2 = document.getElementById("log-level-2");
  const option3 = document.getElementById("log-level-3");

  ///////////////////////////////////////
  ////     F U N C T I O N S   //////////
  ///////////////////////////////////////

  function setSelected(level) {
    document.querySelectorAll(".option").forEach((btn) => btn.classList.remove("selected"));
    const { id, description } = logOptions[level];

    const element = document.getElementById(id);
    if (element) {
      element.classList.add("selected");
    }

    if (descriptionElement) {
      descriptionElement.textContent = description;
    }

    logLevel = level;
    removeSuccessClass();
  }

  function renderExportPaths() {
    exportList.innerHTML = "";
    if (exportPaths.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "No export paths set.";
      exportList.appendChild(empty);
      return;
    }

    exportPaths.forEach((entry, index) => {
      const row = document.createElement("div");
      row.classList.add("export-path-item");

      const nameEl = document.createElement("span");
      nameEl.textContent = `${entry.name}: `;
      nameEl.classList.add("export-path-name");

      const pathEl = document.createElement("span");
      pathEl.textContent = entry.path;
      pathEl.classList.add("export-path-value");

      const removeBtn = document.createElement("button");
      removeBtn.textContent = "✕";
      removeBtn.classList.add("remove-btn");
      removeBtn.onclick = () => {
        exportPaths.splice(index, 1);
        renderExportPaths();
        removeSuccessClass();
      };

      row.appendChild(nameEl);
      row.appendChild(pathEl);
      row.appendChild(removeBtn);

      exportList.appendChild(row);
    });
  }

  function addSuccessClass() {
    saveButton.classList.add("successs");
  }

  function removeSuccessClass() {
    saveButton.classList.remove("successs");
  }

  async function chooseExportFolder() {
    projectNameToAdd = await window.pywebview.api.choose_export_path();
    if (!projectNameToAdd) return;

    const selectedPathInput = document.getElementById("selected-export-path");
    if (selectedPathInput) {
      selectedPathInput.value = projectNameToAdd;
    }
  }


  function addPath() {
    const name = exportName.value.trim();
    if (!name) return alert("Please enter a name for the export path.");

    if(!projectNameToAdd.trim()) return alert("Please choose a path.");
    
    exportPaths.push({ name, path: projectNameToAdd });
    exportName.value = "";
    renderExportPaths();
    removeSuccessClass();
  }

  async function save() {
    try {
      saveButton.classList.add("success");
      await window.pywebview.api.set_settings(exportPaths, logLevel);
      console.log("Settings saved:", {
        export_paths: exportPaths,
        log_level: logLevel,
      });
      addSuccessClass();
    } catch (err) {
      console.warn("Failed to save settings:", err);
    }
  }

  async function reset() {
    try {
      let confirmation = confirm("Are you sure you want to reset the settings?");
      if (!confirmation) return;

      await window.pywebview.api.set_settings([], 1);
      exportPaths = [];
      renderExportPaths();
      setSelected(1);
    } catch (err) {
      console.warn("Failed to reset settings:", err);
    }
  }

  /////////////////////////////////////////////
  ////     E V E N T   L I S T E N E R S   ////
  /////////////////////////////////////////////

  window.addEventListener("pywebviewready", async () => {
    try {
      const { export_paths, log_level } = await window.pywebview.api.get_settings();
      exportPaths = export_paths || [];
      renderExportPaths();
      setSelected(log_level || 2);
      addSuccessClass();
      const plusButton = document.getElementById("add-path-button");
      plusButton.addEventListener("click", addPath);

      option1.addEventListener("click", () => setSelected(1));
      option2.addEventListener("click", () => setSelected(2));
      option3.addEventListener("click", () => setSelected(3));
      addPathButton.addEventListener("click", async () => await chooseExportFolder());
      saveButton.addEventListener("click", async () => await save());
      resetButton.addEventListener("click", async () => await reset());
    } catch (err) {
      console.error("Failed to initialize settings:", err);
    }
  });
});
