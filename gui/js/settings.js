document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pywebviewready", async () => {
    window.pywebview.api
      .get_export_path()
      .then((savedPath) => {
        document.getElementById("export-path").textContent =
          savedPath || "Geen map geselecteerd";
      })
      .catch((err) => {
        console.error("Failed to fetch export path:", err);
      });
  });
});

async function chooseExportFolder() {
  const selectedPath = await window.pywebview.api.choose_export_path();
  document.getElementById("export-path").textContent =
    selectedPath || "Geen map geselecteerd";
}
