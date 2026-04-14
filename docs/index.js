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

  if (
    latestPrerelease &&
    (!latestStable || new Date(latestPrerelease.published_at) > new Date(latestStable.published_at))
  ) {
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

      const windowsSetupAsset = release.assets.find((asset) => asset.name.endsWith(".exe"));
      const windowsPortableAsset = release.assets.find((asset) => asset.name.endsWith("-windows.zip"));
      const linuxAsset = release.assets.find((asset) => asset.name.endsWith("-linux.zip"));

      const windowsSetupLink = downloadModal.querySelector("#download-windows-setup");
      const windowsPortableLink = downloadModal.querySelector("#download-windows-portable");
      const linuxLink = downloadModal.querySelector("#download-linux");

      const windowsSetupCount = downloadModal.querySelector("#windows-setup-download-count");
      const windowsPortableCount = downloadModal.querySelector("#windows-portable-download-count");
      const linuxCount = downloadModal.querySelector("#linux-download-count");

      if (windowsSetupAsset) {
        windowsSetupLink.href = windowsSetupAsset.browser_download_url;
        windowsSetupCount.textContent = windowsSetupAsset.download_count;
        windowsSetupLink.style.display = "flex";
      } else {
        windowsSetupLink.style.display = "none";
      }

      if (windowsPortableAsset) {
        windowsPortableLink.href = windowsPortableAsset.browser_download_url;
        windowsPortableCount.textContent = windowsPortableAsset.download_count;
        windowsPortableLink.style.display = "flex";
      } else {
        windowsPortableLink.style.display = "none";
      }

      if (linuxAsset) {
        linuxLink.href = linuxAsset.browser_download_url;
        linuxCount.textContent = linuxAsset.download_count;
        linuxLink.style.display = "flex";
      } else {
        linuxLink.style.display = "none";
      }

      const aurLink = downloadModal.querySelector("#download-aur");
      const links = [windowsSetupLink, windowsPortableLink, linuxLink, aurLink];
      links.forEach((link) => {
        if (releaseType === "prerelease") {
          link.classList.remove("btn-primary");
          link.classList.add("btn-danger");
        } else {
          link.classList.remove("btn-danger");
          link.classList.add("btn-primary");
        }
      });

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
