const cacheKey = "github-releases";
const cachedData = JSON.parse(localStorage.getItem(cacheKey));
const now = new Date().getTime();

window.latestStableRelease = null;
window.latestPrereleaseRelease = null;

function processReleases(releases) {
  if (!releases || releases.length === 0) {
    return;
  }

  const latestStable = releases.find((release) => !release.prerelease);
  const latestPrerelease = releases.find((release) => release.prerelease);

  if (latestStable) {
    window.latestStableRelease = latestStable;
    const stableLink = document.getElementById("latest-stable");
    const version = latestStable.tag_name.replace("Minify-", ""); // DEPRECATE: bad tag name
    stableLink.innerHTML = `<ion-icon name="download-outline"></ion-icon> Download (${version})`;
  }

  if (latestPrerelease) {
    window.latestPrereleaseRelease = latestPrerelease;
    const downloadButtons = document.getElementById("download-buttons");
    let prereleaseLink = document.getElementById("latest-prerelease");
    if (!prereleaseLink) {
      prereleaseLink = document.createElement("a");
      prereleaseLink.id = "latest-prerelease";
      prereleaseLink.className = "btn btn-danger";
      prereleaseLink.role = "button";
      prereleaseLink.setAttribute("data-bs-toggle", "modal");
      prereleaseLink.setAttribute("data-bs-target", "#downloadModal");
      downloadButtons.appendChild(prereleaseLink);
    }
    const version = latestPrerelease.tag_name.replace("Minify-", ""); // DEPRECATE: bad tag name
    prereleaseLink.innerHTML = `<ion-icon name="download-outline"></ion-icon> Download (${version})`;
    prereleaseLink.setAttribute("data-release-type", "prerelease");
  }

  let totalDownloads = 0;
  releases.forEach((release) => {
    release.assets.forEach((asset) => {
      totalDownloads += asset.download_count;
    });
  });

  const totalDownloadsElement = document.getElementById("total-downloads");
  if (totalDownloadsElement) {
    totalDownloadsElement.textContent = totalDownloads.toLocaleString();
  }
}

if (cachedData && now - cachedData.timestamp < 300000) {
  processReleases(cachedData.releases);
} else {
  fetch("https://api.github.com/repos/egezenn/dota2-minify/releases")
    .then((response) => response.json())
    .then((releases) => {
      localStorage.setItem(cacheKey, JSON.stringify({ timestamp: now, releases: releases }));
      processReleases(releases);
    })
    .catch((error) => {
      if (cachedData) {
        processReleases(cachedData.releases);
      }
      console.error("Error fetching releases:", error);
    });
}

const downloadModal = document.getElementById("downloadModal");
if (downloadModal) {
  downloadModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    const releaseType = button.getAttribute("data-release-type");

    const modalTitle = downloadModal.querySelector(".modal-title");
    const windowsLink = downloadModal.querySelector("#download-windows");
    const linuxLink = downloadModal.querySelector("#download-linux");

    let release;
    if (releaseType === "stable") {
      release = window.latestStableRelease;
    } else {
      release = window.latestPrereleaseRelease;
    }

    if (release) {
      const version = release.tag_name.replace("Minify-", ""); // DEPRECATE: bad tag name
      const typeText = releaseType === "stable" ? "latest stable" : "latest release candidate";
      modalTitle.innerHTML = `Download ${typeText}, ${version}<br><small class="text-muted">Dated ${new Date(release.published_at).toLocaleString()}</small>`;

      const downloadUrlBase = `https://github.com/Egezenn/dota2-minify/releases/download/${release.tag_name}/${release.tag_name}`;
      windowsLink.href = `${downloadUrlBase}-windows.zip`;
      linuxLink.href = `${downloadUrlBase}-linux.zip`;

      if (releaseType === "prerelease") {
        windowsLink.classList.remove("btn-primary");
        windowsLink.classList.add("btn-danger");
        linuxLink.classList.remove("btn-primary");
        linuxLink.classList.add("btn-danger");
      } else {
        windowsLink.classList.remove("btn-danger");
        windowsLink.classList.add("btn-primary");
        linuxLink.classList.remove("btn-danger");
        linuxLink.classList.add("btn-primary");
      }

      const windowsAsset = release.assets.find((asset) => asset.name.endsWith("-windows.zip"));
      const linuxAsset = release.assets.find((asset) => asset.name.endsWith("-linux.zip"));

      const windowsDownloadCount = downloadModal.querySelector("#windows-download-count");
      const linuxDownloadCount = downloadModal.querySelector("#linux-download-count");

      if (windowsAsset) {
        windowsDownloadCount.textContent = windowsAsset.download_count;
      }

      if (linuxAsset) {
        linuxDownloadCount.textContent = linuxAsset.download_count;
      }

      const releaseNotesContainer = downloadModal.querySelector("#release-notes");
      if (releaseType === "stable" && release.body) {
        releaseNotesContainer.style.display = "block";
        releaseNotesContainer.innerHTML = marked.parse(release.body);
      } else {
        releaseNotesContainer.style.display = "none";
        releaseNotesContainer.textContent = "";
      }
    }
  });
}
