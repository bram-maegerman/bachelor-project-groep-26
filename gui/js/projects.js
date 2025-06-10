let projects = [];

document.addEventListener("DOMContentLoaded", () => {
  const addForm = document.getElementById("add-project");
  const closeForm = document.getElementById("close-form");
  const exportPathInput = document.getElementById("export-path");
  const submitButton = document.getElementById("submit");
  const addProjectButton = document.getElementById("add-project-button");

  addProjectButton.addEventListener("click", () => {
    addForm.classList.remove("hidden");
    exportPathInput.value = ""; // Clear the export path input
  });

  async function loadProjects() {
    projects = await window.pywebview.api.get_projects();
    const projectsContainer = document.getElementById("project-list");

    while (projectsContainer.children.length > 2) {
      if (projectsContainer.lastChild.id !== "add-project-button") {
        projectsContainer.removeChild(projectsContainer.lastChild);
      }
    }

    for (const project of Object.keys(projects)) {
      const projectButton = document.createElement("button");
      projectButton.className = "project";
      projectButton.innerHTML = project;
      projectButton.onclick = async () => {
        window.location.href = `project.html?project=${encodeURIComponent(
          project
        )}`;
      };

      projectsContainer.appendChild(projectButton);
    }
  }

  closeForm.addEventListener("click", () => {
    addForm.classList.add("hidden");
  });

  submitButton.addEventListener("click", async () => {
    const nameInput = document.getElementById("project-name");
    const exportPath = exportPathInput.value;

    if (!nameInput.value || !exportPath) {
      alert("Please fill in all fields.");
      return;
    }

    if (projects[nameInput.value]) {
      alert(
        "A project with this name already exists. Please choose a different name."
      );
      return;
    }

    try {
      await window.pywebview.api.add_project(nameInput.value, exportPath);
      addForm.classList.add("hidden");
      nameInput.value = "";
      exportPathInput.value = "";
      await loadProjects();
    } catch (error) {
      console.error("Error creating project:", error);
      alert("Failed to create project. Please try again.");
    }
  });

  window.addEventListener("pywebviewready", () => {
    exportPathInput.addEventListener("click", async () => {
      const path = await window.pywebview.api.choose_folder();
      if (path) {
        exportPathInput.value = path;
      }
    });
    loadProjects();
  });
});
