const modButtonsContainer = document.getElementById("mod-buttons");
const notesModal = new bootstrap.Modal(document.getElementById("notesModal"));
const notesModalLabel = document.getElementById("notesModalLabel");
const notesContent = document.getElementById("notes-content");

const cacheKey = "github-mods";
const cachedData = JSON.parse(localStorage.getItem(cacheKey));
const now = new Date().getTime();

function processMods(mods) {
  modButtonsContainer.innerHTML = "";

  mods.forEach((mod) => {
    const card = document.createElement("div");
    card.className = "card h-100 text-center mod-card";
    card.style.cursor = "pointer";
    card.setAttribute("role", "button");

    const img = document.createElement("img");
    img.src = `https://raw.githubusercontent.com/Egezenn/dota2-minify/main/Minify/mods/${encodeURIComponent(mod)}/image.png`;
    img.className = "card-img-top";
    img.alt = `${mod} image`;
    img.style.objectFit = "cover";
    img.style.height = "140px";
    img.onerror = function () {
      this.style.display = "none";
    };

    const cardBody = document.createElement("div");
    cardBody.className = "card-body d-flex align-items-center justify-content-center";

    const title = document.createElement("h5");
    title.className = "card-title mb-0";
    title.textContent = mod;

    cardBody.appendChild(title);
    card.appendChild(img);
    card.appendChild(cardBody);

    card.addEventListener("click", () => {
      const notesCacheKey = `mod-notes-${mod}`;
      const cachedNotes = JSON.parse(sessionStorage.getItem(notesCacheKey));
      const now = new Date().getTime();
      const imageUrl = `https://raw.githubusercontent.com/Egezenn/dota2-minify/main/Minify/mods/${encodeURIComponent(mod)}/image.png`;
      const imageHtml = `<img src="${imageUrl}" class="mb-3" style="display: block; margin-left: auto; margin-right: auto;" onerror="this.style.display='none'" alt="${mod}">`;

      notesModalLabel.textContent = `${mod} Notes`;
      notesModal.show();

      if (cachedNotes && now - cachedNotes.timestamp < 60000) {
        notesContent.innerHTML = imageHtml + marked.parse(cachedNotes.content);
      } else {
        const notesUrl = `https://raw.githubusercontent.com/Egezenn/dota2-minify/main/Minify/mods/${encodeURIComponent(mod)}/notes.md`;
        notesContent.innerHTML = "<p>Loading...</p>";

        fetch(notesUrl)
          .then((response) => {
            if (!response.ok) {
              throw new Error("Network response was not ok");
            }
            return response.text();
          })
          .then((text) => {
            const enMatch = text.match(/<!-- LANG:en -->([\s\S]*?)(?=<!-- LANG:\w+ -->|$)/i);
            const content = enMatch ? enMatch[1].trim() : text;

            notesContent.innerHTML = imageHtml + marked.parse(content);
            sessionStorage.setItem(notesCacheKey, JSON.stringify({ timestamp: now, content: content }));
          })
          .catch((error) => {
            notesContent.innerHTML = "<p>Could not load notes. The file might not exist for this mod.</p>";
            console.error("Error fetching notes:", error);
          });
      }
    });

    modButtonsContainer.appendChild(card);
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
