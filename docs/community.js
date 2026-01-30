const modsContainer = document.getElementById("mods-container");
const toolsContainer = document.getElementById("tools-container");
const skinsContainer = document.getElementById("skins-container");
const notesModal = new bootstrap.Modal(document.getElementById("notesModal"));
const notesModalLabel = document.getElementById("notesModalLabel");
const notesContent = document.getElementById("notes-content");

const cacheKey = "github-community-data";
const cachedData = JSON.parse(localStorage.getItem(cacheKey));
const now = new Date().getTime();

function createCard(item) {
  const col = document.createElement("div");
  col.className = "col";

  const card = document.createElement("div");
  card.className = "card h-100 text-center mod-card";
  card.style.cursor = "pointer";
  card.setAttribute("role", "button");

  const img = document.createElement("img");
  img.src = `https://raw.githubusercontent.com/Egezenn/dota2-minify-community/main/${encodeURIComponent(item)}/image.png`;
  img.className = "card-img-top";
  img.alt = `${item} image`;
  img.style.objectFit = "cover";
  img.style.height = "140px";
  img.onerror = function () {
    this.style.display = "none";
  };

  const cardBody = document.createElement("div");
  cardBody.className = "card-body d-flex align-items-center justify-content-center";

  const title = document.createElement("h5");
  title.className = "card-title mb-0";
  title.textContent = item;

  cardBody.appendChild(title);
  card.appendChild(img);
  card.appendChild(cardBody);

  card.addEventListener("click", () => {
    const notesCacheKey = `community-mod-notes-${item}`;
    const cachedNotes = JSON.parse(sessionStorage.getItem(notesCacheKey));
    const now = new Date().getTime();

    notesModalLabel.textContent = `${item} Notes`;
    notesModal.show();

    if (cachedNotes && now - cachedNotes.timestamp < 60000) {
      notesContent.innerHTML = cachedNotes.content;
    } else {
      const notesUrl = `https://raw.githubusercontent.com/Egezenn/dota2-minify-community/main/${encodeURIComponent(item)}/notes.html`;
      notesContent.innerHTML = "<p>Loading...</p>";

      fetch(notesUrl)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.text();
        })
        .then((text) => {
          const tempDiv = document.createElement("div");
          tempDiv.innerHTML = text;
          const images = tempDiv.getElementsByTagName("img");
          for (let i = 0; i < images.length; i++) {
            const img = images[i];
            const src = img.getAttribute("src");
            if (src && !src.startsWith("http")) {
              img.src = `https://raw.githubusercontent.com/Egezenn/dota2-minify-community/main/${encodeURIComponent(item)}/${src}`;
            }
          }
          notesContent.innerHTML = tempDiv.innerHTML;
          sessionStorage.setItem(
            notesCacheKey,
            JSON.stringify({
              timestamp: now,
              content: tempDiv.innerHTML,
            }),
          );
        })
        .catch((error) => {
          notesContent.innerHTML = "<p>Could not load notes. The file might not exist for this mod.</p>";
          console.error("Error fetching notes:", error);
        });
    }
  });

  return card;
}

function processData(items, meta) {
  modsContainer.innerHTML = "";
  toolsContainer.innerHTML = "";
  skinsContainer.innerHTML = "";

  items.forEach((item) => {
    const card = createCard(item);
    // Default to 'mod' if not specified or found in meta
    const type = meta[item] && meta[item].type ? meta[item].type : "mod";

    if (type === "tool") {
      toolsContainer.appendChild(card);
    } else if (type === "skin") {
      skinsContainer.appendChild(card);
    } else {
      modsContainer.appendChild(card);
    }
  });

  document.getElementById("mods-section").style.display = modsContainer.hasChildNodes() ? "block" : "none";
  document.getElementById("tools-section").style.display = toolsContainer.hasChildNodes() ? "block" : "none";
  document.getElementById("skins-section").style.display = skinsContainer.hasChildNodes() ? "block" : "none";
}

if (cachedData && now - cachedData.timestamp < 60000) {
  processData(cachedData.items, cachedData.meta);
} else {
  Promise.all([
    fetch("https://api.github.com/repos/egezenn/dota2-minify-community/contents/").then((r) => r.json()),
    fetch("https://raw.githubusercontent.com/Egezenn/dota2-minify-community/main/meta.json")
      .then((r) => r.json())
      .catch(() => ({})),
  ])
    .then(([contentsData, metaData]) => {
      const items = contentsData.filter((item) => item.type === "dir").map((item) => item.name);
      localStorage.setItem(cacheKey, JSON.stringify({ timestamp: now, items: items, meta: metaData }));
      processData(items, metaData);
    })
    .catch((error) => {
      if (cachedData) {
        processData(cachedData.items, cachedData.meta);
      }
      modsContainer.textContent = "Could not load data.";
      console.error("Error fetching data:", error);
    });
}
