(function () {
  "use strict";

  var NAV_SELECTOR = ".nh-patient__nav, .nh-staff__nav, .nh-doctor .nh-staff__sidebar nav";
  var LINK_SELECTOR = ".nh-patient__nav a[href], .nh-staff__nav a[href], .nh-doctor .nh-staff__sidebar nav a[href]";

  function normalizePath(path) {
    var decoded = path || "/";
    try {
      decoded = decodeURIComponent(decoded);
    } catch (_) {
      // Keep the original path if it contains an incomplete escape sequence.
    }
    decoded = decoded.replace(/\/{2,}/g, "/");
    if (decoded.length > 1) decoded = decoded.replace(/\/+$/, "");
    return decoded.toLowerCase();
  }

  function routeFrom(link) {
    var raw = link.getAttribute("href") || "";
    if (!raw || raw.charAt(0) === "#") return null;
    try {
      return normalizePath(new URL(raw, window.location.href).pathname);
    } catch (_) {
      return null;
    }
  }

  function hashFrom(link) {
    var raw = link.getAttribute("href") || "";
    if (!raw) return "";
    if (raw.charAt(0) === "#") return raw.slice(1);
    try {
      var target = new URL(raw, window.location.href);
      if (normalizePath(target.pathname) === normalizePath(window.location.pathname)) {
        return target.hash.slice(1);
      }
    } catch (_) {
      // Ignore invalid links.
    }
    return "";
  }

  function routeMatches(route, current) {
    if (!route) return false;
    if (route === current) return true;
    if (route === "/") return current === "/";
    return current.indexOf(route + "/") === 0;
  }

  function markActive(nav, selected) {
    nav.querySelectorAll("a[href]").forEach(function (link) {
      var active = link === selected;
      link.classList.toggle("is-active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function updateNavigation(nav) {
    var links = Array.prototype.slice.call(nav.querySelectorAll("a[href]"));
    if (!links.length) return;

    var currentPath = normalizePath(window.location.pathname);
    var currentHash = window.location.hash.replace(/^#/, "");
    var candidates = links.map(function (link) {
      var route = routeFrom(link);
      return {
        link: link,
        route: route,
        routeMatch: routeMatches(route, currentPath),
        routeLength: route ? route.length : 0,
        hash: hashFrom(link)
      };
    });

    var pathMatches = candidates.filter(function (item) { return item.routeMatch; });
    var selected = null;
    if (pathMatches.length) {
      pathMatches.sort(function (a, b) { return b.routeLength - a.routeLength; });
      selected = pathMatches[0].link;
    } else if (currentHash) {
      var hashMatch = candidates.find(function (item) { return item.hash === currentHash; });
      if (hashMatch) selected = hashMatch.link;
    }

    if (!selected) {
      selected = links.find(function (link) { return link.classList.contains("is-active"); }) || null;
    }
    if (!selected) {
      selected = links.find(function (link) { return hashFrom(link) !== ""; }) || null;
    }
    markActive(nav, selected);
  }

  function updateAllNavigations() {
    document.querySelectorAll(NAV_SELECTOR).forEach(updateNavigation);
  }

  function initialize() {
    updateAllNavigations();

    // Capture before page-specific click handlers, smooth-scroll scripts, or delegated handlers.
    document.addEventListener("click", function (event) {
      var target = event.target;
      if (target && target.nodeType !== 1) target = target.parentElement;
      if (!target || typeof target.closest !== "function") return;
      var link = target.closest(LINK_SELECTOR);
      if (!link) return;
      var nav = link.closest(NAV_SELECTOR);
      if (nav) markActive(nav, link);
    }, true);

    // Also handle navigation markup that is rendered or replaced after initial page load.
    if (window.MutationObserver) {
      var observer = new MutationObserver(function () {
        updateAllNavigations();
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }

  window.addEventListener("hashchange", updateAllNavigations);
  window.addEventListener("popstate", updateAllNavigations);
})();
