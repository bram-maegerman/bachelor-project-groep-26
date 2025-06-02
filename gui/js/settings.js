document.addEventListener("DOMContentLoaded", () => {
  ///////////////////////////////////////////////
  ////     G L O B A L   V A R I A B L E S   ////
  ///////////////////////////////////////////////

  let logLevel = 2; // Default log level
  let exportPath = ""; // Default export path
  const logOptions = {
    1: {
      id: "log-level-1",
      description: "Only warnings are shown",
    },
    2: {
      id: "log-level-2",
      description: "Warnings and info messages are shown",
    },
    3: {
      id: "log-level-3",
      description: "All logs are shown",
    },
  };

  /////////////////////////////////////
  ////     E L E M E N T S   //////////
  /////////////////////////////////////

  const saveButton = document.getElementById("save-button");
  const resetButton = document.getElementById("reset-button");

  const exportPathElement = document.getElementById("export-path");
  const exportFolderButton = document.getElementById("choose-export-folder");

  const descriptionElement = document.getElementById("log-level-description");

  const option1 = document.getElementById("log-level-1");
  const option2 = document.getElementById("log-level-2");
  const option3 = document.getElementById("log-level-3");

  ///////////////////////////////////////
  ////     F U N C T I O N S   //////////
  ///////////////////////////////////////

  function setSelected(number) {
    let selectedElement = document.querySelector(".selected");
    if (selectedElement) {
      selectedElement.classList.remove("selected");
    }

    const { id, description } = logOptions[number];

    const element = document.getElementById(id);
    if (element) {
      element.classList.add("selected");
    }

    if (descriptionElement) {
      descriptionElement.textContent = description;
    }

    // Update global log level variable
    logLevel = number;
    removeSuccesssClass();
  }

  function setExportPath(path) {
    exportPathElement.textContent = path || "No file selected";
    exportPath = path; // Update global export path variable
    removeSuccesssClass();
  }

  function addSuccesssClass() {
    saveButton.classList.add("successs");
  }

  function removeSuccesssClass() {
    saveButton.classList.remove("successs");
  }

  async function chooseExportFolder() {
    const selectedPath = await window.pywebview.api.choose_export_path();
    document.getElementById("export-path").textContent =
      selectedPath || "No file selected";
    setExportPath(selectedPath);
  }

  async function save() {
    try {
      saveButton.classList.add("success");
      await window.pywebview.api.set_settings(exportPath, logLevel);
      console.log("Settings saved:", {
        export_path: exportPath,
        log_level: logLevel,
      });

      addSuccesssClass();
    } catch (err) {
      console.warn("Failed to save settings:", err);
    }
  }

  async function reset() {
    try {
      let confirmation = confirm(
        "Are you sure you want to reset the settings?"
      );
      if (!confirmation) {
        return;
      } else {
        await window.pywebview.api.set_settings("", 1);
        setExportPath("");
        setSelected(1);
      }
    } catch (err) {
      console.warn("Failed to reset settings:", err);
    }
  }

  /////////////////////////////////////////////
  ////     E V E N T   L I S T E N E R S   ////
  /////////////////////////////////////////////

  window.addEventListener("pywebviewready", async () => {
    try {
      const { export_path, log_level } =
        await window.pywebview.api.get_settings();
      let path = export_path || exportPath;

      setExportPath(path);

      let level = log_level || logLevel;
      setSelected(level);

      addSuccesssClass();

      option1.addEventListener("click", () => setSelected(1));
      option2.addEventListener("click", () => setSelected(2));
      option3.addEventListener("click", () => setSelected(3));

      // Set export path in the UI
      exportFolderButton.addEventListener(
        "click",
        async () => await chooseExportFolder()
      );

      saveButton.addEventListener("click", async () => await save());

      resetButton.addEventListener("click", async () => await reset());
    } catch (err) {
      console.error("Failed to initialize settings:", err);
    }
  });
});
