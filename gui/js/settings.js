document.addEventListener("DOMContentLoaded", () => {
  ///////////////////////////////////////////////
  ////     G L O B A L   V A R I A B L E S   ////
  ///////////////////////////////////////////////

  let logLevel = 2;

  const logOptions = {
    1: { id: "log-level-1", description: "Only warnings are shown" },
    2: {
      id: "log-level-2",
      description: "Warnings and info messages are shown",
    },
    3: { id: "log-level-3", description: "All logs are shown" },
  };

  /////////////////////////////////////
  ////     E L E M E N T S   //////////
  /////////////////////////////////////

  const saveButton = document.getElementById("save-button");
  const resetButton = document.getElementById("reset-button");
  const addPathButton = document.getElementById("choose-new-export-folder");
  const descriptionElement = document.getElementById("log-level-description");
  const option1 = document.getElementById("log-level-1");
  const option2 = document.getElementById("log-level-2");
  const option3 = document.getElementById("log-level-3");

  /////////////////////////////////
  ////     F U N C T I O N S   ////
  /////////////////////////////////

  function setSelected(level) {
    document
      .querySelectorAll(".option")
      .forEach((btn) => btn.classList.remove("selected"));
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

  function addSuccessClass() {
    saveButton.classList.add("successs");
  }

  function removeSuccessClass() {
    saveButton.classList.remove("successs");
  }

  async function save() {
    try {
      saveButton.classList.add("success");
      await window.pywebview.api.set_settings(logLevel);

      addSuccessClass();
    } catch (err) {
      console.warn("Failed to save settings:", err);
    }
  }

  async function reset() {
    try {
      let confirmation = confirm(
        "Are you sure you want to reset the settings?"
      );
      if (!confirmation) return;

      await window.pywebview.api.set_settings(1);
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
      const { log_level } = await window.pywebview.api.get_settings();
      setSelected(log_level || 2);
      addSuccessClass();
      const plusButton = document.getElementById("add-path-button");
      plusButton.addEventListener("click", addPath);

      option1.addEventListener("click", () => setSelected(1));
      option2.addEventListener("click", () => setSelected(2));
      option3.addEventListener("click", () => setSelected(3));
      addPathButton.addEventListener(
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
