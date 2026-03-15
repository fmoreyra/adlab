/**
 * AdLab - Main application JavaScript
 * Step 21: In-app notifications (bell + dropdown + realtime via Sockudo)
 */

import Pusher from "pusher-js";

(function () {
  "use strict";

  const container = document.getElementById("notifications-container");
  if (!container) return;

  const apiList = container.dataset.apiList;
  const apiUnreadCount = container.dataset.apiUnreadCount;
  const apiReadAll = container.dataset.apiReadAll;
  const bell = document.getElementById("notifications-bell");
  const badge = document.getElementById("notifications-badge");
  const dropdown = document.getElementById("notifications-dropdown");
  const listEl = document.getElementById("notifications-list");
  const loadingEl = document.getElementById("notifications-loading");
  const markAllBtn = document.getElementById("notifications-mark-all");

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  function fetchJson(url, options = {}) {
    const opts = {
      headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
      ...options,
    };
    if (options.method && options.method !== "GET") {
      opts.headers["Content-Type"] = "application/json";
      opts.headers["X-CSRFToken"] = getCsrfToken();
    }
    return fetch(url, opts).then((r) => r.json());
  }

  function postJson(url, body = {}) {
    return fetchJson(url, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  function updateBadge(count) {
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? "99+" : String(count);
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  }

  function loadUnreadCount() {
    if (!apiUnreadCount) return;
    fetchJson(apiUnreadCount)
      .then((data) => updateBadge(data.count || 0))
      .catch(() => {});
  }

  function renderNotification(n) {
    const isRead = n.is_read;
    const item = document.createElement("a");
    item.href = n.link_url || "#";
    item.className =
      "block p-3 hover:bg-purple-50 transition " +
      (isRead ? "bg-gray-50 text-gray-600" : "bg-white text-gray-900");
    item.dataset.id = n.id;
    item.innerHTML = `
      <p class="font-medium text-sm">${escapeHtml(n.title)}</p>
      ${n.body ? `<p class="text-xs mt-1 text-gray-500 line-clamp-2">${escapeHtml(n.body)}</p>` : ""}
      <p class="text-xs mt-1 text-gray-400">${formatDate(n.created_at)}</p>
    `;
    if (!isRead) {
      item.addEventListener("click", (e) => {
        if (n.link_url) return;
        e.preventDefault();
        markAsRead(n.id);
      });
    }
    if (n.link_url) {
      item.addEventListener("click", () => markAsRead(n.id));
    }
    return item;
  }

  function escapeHtml(s) {
    if (!s) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function formatDate(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("es-AR", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  function markAsRead(id) {
    const url = apiList.replace(/\/?$/, "") + "/" + id + "/read/";
    postJson(url)
      .then(() => {
        loadUnreadCount();
        loadList();
      })
      .catch(() => {});
  }

  function loadList() {
    if (!apiList || !listEl) return;
    loadingEl.classList.remove("hidden");
    listEl.innerHTML = "";
    listEl.appendChild(loadingEl);
    fetchJson(apiList)
      .then((data) => {
        loadingEl.classList.add("hidden");
        loadingEl.remove();
        const notifications = data.notifications || [];
        if (notifications.length === 0) {
          const empty = document.createElement("div");
          empty.className = "p-4 text-center text-gray-500 text-sm";
          empty.textContent = "No hay notificaciones";
          listEl.appendChild(empty);
        } else {
          notifications.forEach((n) => listEl.appendChild(renderNotification(n)));
        }
      })
      .catch(() => {
        loadingEl.textContent = "Error al cargar";
      });
  }

  function toggleDropdown() {
    const isOpen = !dropdown.classList.contains("hidden");
    if (isOpen) {
      dropdown.classList.add("hidden");
      document.removeEventListener("click", closeOnClickOutside);
    } else {
      dropdown.classList.remove("hidden");
      loadList();
      document.addEventListener("click", closeOnClickOutside);
    }
  }

  function closeOnClickOutside(e) {
    if (
      dropdown &&
      !dropdown.contains(e.target) &&
      !bell.contains(e.target)
    ) {
      dropdown.classList.add("hidden");
      document.removeEventListener("click", closeOnClickOutside);
    }
  }

  bell.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleDropdown();
  });

  markAllBtn.addEventListener("click", (e) => {
    e.preventDefault();
    postJson(apiReadAll)
      .then(() => {
        loadUnreadCount();
        loadList();
      })
      .catch(() => {});
  });

  loadUnreadCount();

  // Realtime: connect to Sockudo (Pusher-compatible) when config is present
  const sockudoEl = document.getElementById("sockudo-config");
  if (sockudoEl) {
    try {
      const cfg = JSON.parse(sockudoEl.textContent);
      if (cfg && cfg.enabled && cfg.app_key && cfg.user_id) {
        const pusherOpts = {
          cluster: "us1",
          forceTLS: cfg.ws_use_tls,
          enabledTransports: ["ws", "wss"],
          channelAuthorization: {
            endpoint: cfg.auth_endpoint,
            transport: "ajax",
            params: {},
            headers: { "X-CSRFToken": getCsrfToken() },
          },
        };
        if (cfg.ws_host) {
          pusherOpts.wsHost = cfg.ws_host;
          pusherOpts.wsPort = cfg.ws_port || (cfg.ws_use_tls ? 443 : 6001);
          pusherOpts.wssPort = cfg.ws_port || 443;
          pusherOpts.disableStats = true;
        }
        const pusher = new Pusher(cfg.app_key, pusherOpts);
        const channel = pusher.subscribe(`private-user-${cfg.user_id}`);
        channel.bind("notification.created", () => {
          loadUnreadCount();
          if (!dropdown.classList.contains("hidden")) {
            loadList();
          }
        });
      }
    } catch (e) {
      console.warn("Sockudo realtime init failed:", e);
    }
  }
})();
