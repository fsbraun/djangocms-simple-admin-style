// update-notification.js
// Checks for available django CMS updates and displays a notification in the admin area

const CMS_UPDATE_URL = "https://pypi.org/pypi/django-cms/json";

function getCurrentVersionFromScript() {
  // Get the current django CMS version from the data attribute of the script tag
  const script =
    document.currentScript ||
    Array.from(document.querySelectorAll("script")).find(
      (s) => s.src && s.src.includes("update-notification.js"),
    );
  return script ? script.dataset.cmsVersion : null;
}

function getCheckTypeFromScript() {
  // Get the version check type from the data attribute of the script tag
  const script =
    document.currentScript ||
    Array.from(document.querySelectorAll("script")).find(
      (s) => s.src && s.src.includes("update-notification.js"),
    );
  return script ? script.dataset.versionCheckType : "patch";
}

const CURRENT_VERSION = getCurrentVersionFromScript();
const CMS_VERSION_CHECK_TYPE = getCheckTypeFromScript();

function setCookie(name, value, days) {
  // Sets a cookie with expiration in days
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function getCookie(name) {
  // Gets a cookie value by name
  return document.cookie.split("; ").reduce((r, v) => {
    const parts = v.split("=");
    return parts[0] === name ? decodeURIComponent(parts[1]) : r;
  }, "");
}

function getNewerReleases(data, currentVersion, checkType) {
  const releases = Object.keys(data.releases).filter(
    (version) => data.releases[version][0] && !data.releases[version][0].yanked,
  );

  return releases.filter((version) =>
    isNewerVersion(version, currentVersion, checkType),
  );
}

async function checkCmsUpdate() {
  if (!CURRENT_VERSION) return;
  try {
    const response = await fetch(CMS_UPDATE_URL);
    if (!response.ok) throw new Error("Error fetching version info");
    const data = await response.json();
    const latestVersion = getNewerReleases(
      data,
      CURRENT_VERSION,
      CMS_VERSION_CHECK_TYPE,
    ).sort((a, b) => {
      // Sort versions descending
      const aParts = a.split(".").map(Number);
      const bParts = b.split(".").map(Number);
      for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
        const aNum = aParts[i] || 0;
        const bNum = bParts[i] || 0;
        if (aNum !== bNum) return bNum - aNum;
      }
      return 0;
    })[0];
    if (!latestVersion) return;
    // Check if notification for this version was closed
    const closedKey = `cms-update-closed-${latestVersion}`;
    if (getCookie(closedKey)) return;
    if (
      isNewerVersion(latestVersion, CURRENT_VERSION, CMS_VERSION_CHECK_TYPE)
    ) {
      showUpdateNotification(latestVersion);
    }
  } catch (error) {
    console.error("Update check failed:", error);
  }
}

function isNewerVersion(latest, current, checkType = "patch") {
  // Compares two version strings, e.g. '3.11.0' > '3.10.0'
  const latestParts = latest.split(".").map((x) => Number(x) || 0);
  const currentParts = current.split(".").map((x) => Number(x) || 0);

  if (checkType === "minor" || checkType === "patch") {
    if (latestParts[0] !== currentParts[0]) {
      return false;
    }
  }
  if (checkType === "patch") {
    if (latestParts[1] !== currentParts[1]) {
      return false;
    }
  }

  for (let i = 0; i < Math.max(latestParts.length, currentParts.length); i++) {
    const l = latestParts[i] || 0;
    const c = currentParts[i] || 0;
    if (l > c) return true;
    if (l < c) return false;
  }
  return false;
}

function showUpdateNotification(latestVersion) {
  const template = document.getElementById("cms-update-template");
  if (!template) return;
  const clone = template.content
    ? template.content.cloneNode(true)
    : document.createElement("div");
  // Set old version
  const oldVersionElem = clone.querySelector(".js-current-version");
  if (oldVersionElem) oldVersionElem.textContent = CURRENT_VERSION;
  // Set new version
  const latestVersionElem = clone.querySelector(".js-latest-version");
  if (latestVersionElem) latestVersionElem.textContent = latestVersion;
  // Set release notes link
  const releaseLink = clone.querySelector(".js-release-notes-link");
  if (releaseLink) {
    const splitVersion = latestVersion.split(".");
    releaseLink.href = `https://docs.django-cms.org/en/release-${splitVersion[0]}.${splitVersion[1]}.x/upgrade/${latestVersion}.html`;
  }
  // Add close button functionality

  const closeBtn = clone.querySelector(".close");
  if (closeBtn)
    closeBtn.addEventListener("click", function (e) {
      e.preventDefault();
      closeBtn.parentElement.style.display = "none";
      // Store closed state in cookie for 14 days
      const closedKey = `cms-update-closed-${latestVersion}`;
      setCookie(closedKey, "1", 14);
    });
  // Insert notification into admin area
  const adminContent = document.querySelector("#content-main");
  if (adminContent) {
    adminContent.insertBefore(clone, adminContent.firstChild);
  }
}

// Start the check after DOM load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", checkCmsUpdate);
} else {
  checkCmsUpdate();
}
