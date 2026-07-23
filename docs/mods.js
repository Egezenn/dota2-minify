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
    img.src = Mirror.getRawUrl("Minify/mods/" + encodeURIComponent(mod) + "/preview.jpg");
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
      const imageUrl = Mirror.getRawUrl("Minify/mods/" + encodeURIComponent(mod) + "/preview.jpg");
      const imageHtml = `<img src="${imageUrl}" class="mb-3" style="display: block; margin-left: auto; margin-right: auto;" onerror="this.style.display='none'" alt="${mod}">`;

      notesModalLabel.textContent = `${mod} Notes`;
      notesModal.show();

      if (cachedNotes && now - cachedNotes.timestamp < 60000) {
        notesContent.innerHTML =
          imageHtml + marked.parse(cachedNotes.content).replace(/<p>\s*!!:\s*/g, '<p class="note-emphasized">');
      } else {
        const notesUrl = Mirror.getRawUrl("Minify/mods/" + encodeURIComponent(mod) + "/notes.md");
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

            notesContent.innerHTML =
              imageHtml + marked.parse(content).replace(/<p>\s*!!:\s*/g, '<p class="note-emphasized">');
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
  const fetchMods = (retry = true) => {
    fetch(Mirror.getContentsApiUrl("Minify/mods"))
      .then((response) => {
        if (response.status !== 200) {
          if (retry) {
            setTimeout(() => fetchMods(false), 3000);
            return null;
          }
          throw new Error(`HTTP status ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (!data) return;
        if (Array.isArray(data)) {
          const mods = data
            .filter((item) => item.type === "dir" && item.name !== "#base" && item.name !== "User Styles")
            .map((item) => item.name);

          if (mods.length > 0) {
            localStorage.setItem(cacheKey, JSON.stringify({ timestamp: new Date().getTime(), mods: mods }));
            processMods(mods);
          } else {
            throw new Error("No mods found");
          }
        } else {
          throw new Error("Invalid mods data");
        }
      })
      .catch((error) => {
        if (cachedData) {
          processMods(cachedData.mods);
        }
        modButtonsContainer.textContent = "Could not load mods list.";
        console.error("Error fetching mods list:", error);
      });
  };
  fetchMods();
}
