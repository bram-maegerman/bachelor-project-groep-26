document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", async () => {
    try {
      // Load and show export path
      const savedPath = await window.pywebview.api.get_export_path();
      document.getElementById("export-path").textContent =
        savedPath || "Geen map geselecteerd";

      // Load and set log level select
      const logLevel = await window.pywebview.api.get_log_level();
      const logLevelSelect = document.getElementById("log-level");
      if (logLevelSelect) {
        logLevelSelect.value = logLevel.toString();
        // Listen for changes to update backend
        logLevelSelect.addEventListener("change", async (event) => {
          const newLevel = parseInt(event.target.value);
          try {
            await window.pywebview.api.set_log_level(newLevel);
            console.log("Log level updated to:", newLevel);
          } catch (e) {
            console.error("Failed to update log level:", e);
          }
        });
      }
    } catch (err) {
      console.error("Failed to initialize settings:", err);
    }
  });
});

async function chooseExportFolder() {
  const selectedPath = await window.pywebview.api.choose_export_path();
  document.getElementById("export-path").textContent =
    selectedPath || "Geen map geselecteerd";
}
