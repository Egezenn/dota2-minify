const modButtonsContainer = document.getElementById("mod-buttons");
const notesModal = new bootstrap.Modal(document.getElementById("notesModal"));
const notesModalLabel = document.getElementById("notesModalLabel");
const notesContent = document.getElementById("notes-content");

const cacheKey = "github-mods";
const cachedData = JSON.parse(localStorage.getItem(cacheKey));
const now = new Date().getTime();

function processMods(mods) {
  mods.forEach((mod) => {
    const button = document.createElement("button");
    button.className = "btn btn-info";
    button.textContent = mod;
    button.addEventListener("click", () => {
      const notesCacheKey = `mod-notes-${mod}`;
      const cachedNotes = JSON.parse(sessionStorage.getItem(notesCacheKey));
      const now = new Date().getTime();

      notesModalLabel.textContent = `${mod} Notes`;
      notesModal.show();

      if (cachedNotes && now - cachedNotes.timestamp < 60000) {
        notesContent.innerHTML = marked.parse(cachedNotes.content);
      } else {
        const notesUrl = `https://raw.githubusercontent.com/Egezenn/dota2-minify/main/Minify/mods/${encodeURIComponent(mod)}/notes_en.txt`;
        notesContent.innerHTML = "<p>Loading...</p>";

        fetch(notesUrl)
          .then((response) => {
            if (!response.ok) {
              throw new Error("Network response was not ok");
            }
            return response.text();
          })
          .then((text) => {
            notesContent.innerHTML = marked.parse(text);
            sessionStorage.setItem(notesCacheKey, JSON.stringify({ timestamp: now, content: text }));
          })
          .catch((error) => {
            notesContent.innerHTML = "<p>Could not load notes. The file might not exist for this mod.</p>";
            console.error("Error fetching notes:", error);
          });
      }
    });
    modButtonsContainer.appendChild(button);
  });
}

if (cachedData && now - cachedData.timestamp < 60000) {
  processMods(cachedData.mods);
} else {
  fetch("https://api.github.com/repos/egezenn/dota2-minify/contents/Minify/mods")
    .then((response) => response.json())
    .then((data) => {
      const mods = data
        .filter((item) => item.type === "dir" && item.name !== "#base" && item.name !== "User Styles")
        .map((item) => item.name);
      localStorage.setItem(cacheKey, JSON.stringify({ timestamp: now, mods: mods }));
      processMods(mods);
    })
    .catch((error) => {
      if (cachedData) {
        processMods(cachedData.mods);
      }
      modButtonsContainer.textContent = "Could not load mods list.";
      console.error("Error fetching mods list:", error);
    });
}
