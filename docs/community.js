const modsContainer = document.getElementById("mods-container");
const themesContainer = document.getElementById("themes-container");
const pluginsContainer = document.getElementById("plugins-container");
const notesModal = new bootstrap.Modal(document.getElementById("notesModal"));
const notesModalLabel = document.getElementById("notesModalLabel");
const notesContent = document.getElementById("notes-content");

const cacheKey = "community-registry-data";
const cachedData = JSON.parse(localStorage.getItem(cacheKey));
const now = new Date().getTime();

function renderNotes(item, markdown) {
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = marked.parse(markdown).replace(/<p>\s*!!:\s*/g, '<p class="note-emphasized">');

  const images = tempDiv.getElementsByTagName("img");
  for (let i = 0; i < images.length; i++) {
    const src = images[i].getAttribute("src");
    if (src && !/^(https?:)?\/\//.test(src)) {
      images[i].src = new URL(src, item.notes).href;
    }
  }

  notesContent.innerHTML = tempDiv.innerHTML;
}

function openNotes(item) {
  notesModalLabel.textContent = `${item.name} Notes`;
  notesModal.show();

  if (!item.notes) {
    notesContent.innerHTML = "<p>No notes available for this mod.</p>";
    return;
  }

  const notesCacheKey = `community-mod-notes-${item.notes}`;
  const cachedNotes = JSON.parse(sessionStorage.getItem(notesCacheKey));
  const now = new Date().getTime();

  if (cachedNotes && now - cachedNotes.timestamp < 60000) {
    renderNotes(item, cachedNotes.content);
    return;
  }

  notesContent.innerHTML = "<p>Loading...</p>";

  fetch(item.notes)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.text();
    })
    .then((text) => {
      const enMatch = text.match(/<!-- LANG:en -->([\s\S]*?)(?=<!-- LANG:\w+ -->|$)/i);
      const content = enMatch ? enMatch[1].trim() : text;
      renderNotes(item, content);
      sessionStorage.setItem(notesCacheKey, JSON.stringify({ timestamp: now, content: content }));
    })
    .catch((error) => {
      notesContent.innerHTML = "<p>Could not load notes. The file might not exist for this mod.</p>";
      console.error("Error fetching notes:", error);
    });
}

function createCard(item) {
  const card = document.createElement("div");
  card.className = "card h-100 text-center mod-card";
  card.style.cursor = "pointer";
  card.setAttribute("role", "button");

  if (item.preview) {
    const img = document.createElement("img");
    img.src = item.preview;
    img.className = "card-img-top";
    img.alt = `${item.name} preview`;
    img.style.objectFit = "cover";
    img.style.height = "140px";
    img.onerror = function () {
      this.style.display = "none";
    };
    card.appendChild(img);
  }

  const cardBody = document.createElement("div");
  cardBody.className = "card-body d-flex align-items-center justify-content-center";

  const title = document.createElement("h5");
  title.className = "card-title mb-0";
  title.textContent = item.name;

  cardBody.appendChild(title);
  card.appendChild(cardBody);

  if (item.repo || item["latest-asset"]) {
    const footer = document.createElement("div");
    footer.className = "card-footer d-flex justify-content-center gap-3";

    if (item.repo) {
      const repoLink = document.createElement("a");
      repoLink.href = item.repo;
      repoLink.target = "_blank";
      repoLink.rel = "noopener noreferrer";
      repoLink.textContent = "Repo";

      const repoItem = document.createElement("span");
      repoItem.className = "d-inline-flex align-items-center gap-1";
      repoItem.addEventListener("click", (e) => e.stopPropagation());
      const repoIcon = document.createElement("ion-icon");
      repoIcon.name = "logo-github";
      repoItem.appendChild(repoIcon);
      repoItem.appendChild(repoLink);
      footer.appendChild(repoItem);
    }

    if (item["latest-asset"]) {
      const downloadLink = document.createElement("a");
      downloadLink.href = item["latest-asset"];
      downloadLink.textContent = "Download";

      const downloadItem = document.createElement("span");
      downloadItem.className = "d-inline-flex align-items-center gap-1";
      downloadItem.addEventListener("click", (e) => e.stopPropagation());
      const downloadIcon = document.createElement("ion-icon");
      downloadIcon.name = "download-outline";
      downloadItem.appendChild(downloadIcon);
      downloadItem.appendChild(downloadLink);
      footer.appendChild(downloadItem);
    }

    card.appendChild(footer);
  }

  card.addEventListener("click", () => openNotes(item));

  return card;
}

function processData(items) {
  modsContainer.innerHTML = "";
  themesContainer.innerHTML = "";
  pluginsContainer.innerHTML = "";

  items.forEach((item) => {
    const type = item.type || "mod";
    const card = createCard(item);

    if (type === "theme") {
      themesContainer.appendChild(card);
    } else if (type === "plugin") {
      pluginsContainer.appendChild(card);
    } else {
      modsContainer.appendChild(card);
    }
  });

  document.getElementById("mods-section").style.display = modsContainer.hasChildNodes() ? "block" : "none";
  document.getElementById("themes-section").style.display = themesContainer.hasChildNodes() ? "block" : "none";
  document.getElementById("plugins-section").style.display = pluginsContainer.hasChildNodes() ? "block" : "none";
}

if (cachedData && now - cachedData.timestamp < 60000) {
  processData(cachedData.items);
} else {
  const fetchData = (retry = true) => {
    fetch(Mirror.getCommunityRegistryUrl())
      .then((response) => {
        if (!response.ok) {
          if (retry) throw { retry: true };
          throw new Error(`HTTP status ${response.status}`);
        }
        return response.json();
      })
      .then((registry) => {
        if (Array.isArray(registry) && registry.length > 0) {
          localStorage.setItem(
            cacheKey,
            JSON.stringify({
              timestamp: new Date().getTime(),
              items: registry,
            }),
          );
          processData(registry);
        } else {
          throw new Error("Invalid community registry data");
        }
      })
      .catch((error) => {
        if (error.retry) {
          setTimeout(() => fetchData(false), 3000);
          return;
        }
        if (cachedData) {
          processData(cachedData.items);
        } else {
          modsContainer.textContent = "Could not load data.";
        }
        console.error("Error fetching data:", error);
      });
  };
  fetchData();
}
