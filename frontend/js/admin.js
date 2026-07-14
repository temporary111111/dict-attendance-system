import { apiRequest } from "./api.js";
import { logout, requireAdmin } from "./auth.js";

const app = document.querySelector("#admin-app");
const appLoading = document.querySelector("#app-loading");
const root = document.querySelector("#view-root");
const pageTitle = document.querySelector("#page-title");
const refreshButton = document.querySelector("#refresh-button");
const sidebar = document.querySelector("#sidebar");
const scrim = document.querySelector("#sidebar-scrim");

const state = {
  user: null,
  view: "dashboard",
  auditPage: 1,
};

const views = {
  dashboard: { title: "Dashboard", load: renderDashboard },
  programs: { title: "Programs", load: renderPrograms },
  events: { title: "Events", load: renderEvents },
  audit: { title: "Audit Logs", load: renderAuditLogs, superAdminOnly: true },
};

function escapeSelector(value) {
  return CSS.escape(String(value));
}

function setText(selector, value, parent = document) {
  const element = parent.querySelector(selector);
  if (element) element.textContent = value ?? "";
  return element;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-PH").format(Number(value || 0));
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-PH", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-PH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatRole(roleName) {
  return roleName === "super_admin" ? "Super Admin" : "Program Admin";
}

function initials(fullName) {
  return fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function badge(status) {
  const span = document.createElement("span");
  span.className = `badge badge-${String(status).toLowerCase()}`;
  span.textContent = String(status).replaceAll("_", " ");
  return span;
}

function cell(text, className = "") {
  const td = document.createElement("td");
  td.className = className;
  td.textContent = text ?? "-";
  return td;
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.querySelector("#toast-region").append(toast);
  window.setTimeout(() => toast.remove(), 3500);
}

function renderLoading() {
  root.innerHTML = `
    <div class="panel loading-state" role="status">
      <div class="large-spinner"></div>
      <span>Loading data...</span>
    </div>`;
}

function renderError(error, retry) {
  root.innerHTML = `
    <div class="panel error-state">
      <div class="state-symbol" aria-hidden="true">!</div>
      <strong>Unable to load this view</strong>
      <span id="view-error-message"></span>
      <button id="retry-view" class="secondary-button" type="button">Try again</button>
    </div>`;
  setText("#view-error-message", error.message);
  document.querySelector("#retry-view").addEventListener("click", retry);
}

function renderEmpty(container, title, message) {
  container.innerHTML = `
    <div class="empty-state">
      <div class="state-symbol" aria-hidden="true">−</div>
      <strong></strong>
      <span></span>
    </div>`;
  setText("strong", title, container);
  setText("span", message, container);
}

function statusBars(container, values) {
  const maximum = Math.max(1, ...Object.values(values));
  for (const [status, total] of Object.entries(values)) {
    const row = document.createElement("div");
    row.className = "status-bar-row";
    row.innerHTML = `
      <span class="status-name"></span>
      <div class="status-track"><div class="status-fill"></div></div>
      <span class="status-bar-value"></span>`;
    setText(".status-name", status.replaceAll("_", " "), row);
    const fill = row.querySelector(".status-fill");
    fill.classList.add(status);
    fill.style.width = `${Math.round((Number(total) / maximum) * 100)}%`;
    setText(".status-bar-value", formatNumber(total), row);
    container.append(row);
  }
}

async function renderDashboard() {
  renderLoading();
  try {
    const response = await apiRequest("/dashboard/summary");
    const data = response.data;
    root.innerHTML = `
      <section class="view-intro">
        <div><h2>Operational overview</h2><p id="dashboard-scope"></p></div>
      </section>
      <section class="summary-grid" aria-label="Summary totals">
        <article class="summary-card"><span class="summary-label">Active programs</span><strong id="program-total" class="summary-value"></strong></article>
        <article class="summary-card green"><span class="summary-label">Visible events</span><strong id="event-total" class="summary-value"></strong></article>
        <article class="summary-card amber"><span class="summary-label">Attendance records</span><strong id="attendance-total" class="summary-value"></strong></article>
      </section>
      <section class="dashboard-grid">
        <article class="panel">
          <header class="panel-header"><h3>Attendance status</h3></header>
          <div id="attendance-bars" class="panel-body status-bars"></div>
        </article>
        <article class="panel">
          <header class="panel-header"><h3>Recent events</h3></header>
          <div id="recent-events" class="table-wrap"></div>
        </article>
      </section>`;

    setText(
      "#dashboard-scope",
      state.user.role.role_name === "super_admin"
        ? "System-wide active records"
        : "Records under your active program assignments",
    );
    setText("#program-total", formatNumber(data.totals.programs));
    setText("#event-total", formatNumber(data.totals.events));
    setText("#attendance-total", formatNumber(data.totals.attendance_records));
    statusBars(document.querySelector("#attendance-bars"), data.attendance_by_status);

    const recentContainer = document.querySelector("#recent-events");
    if (!data.recent_events.length) {
      renderEmpty(recentContainer, "No recent events", "Visible events will appear here.");
      return;
    }
    recentContainer.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Event</th><th>Date</th><th>Status</th><th class="numeric-cell">Valid</th></tr></thead>
        <tbody></tbody>
      </table>`;
    const tbody = recentContainer.querySelector("tbody");
    for (const event of data.recent_events) {
      const tr = document.createElement("tr");
      const eventCell = document.createElement("td");
      const name = document.createElement("div");
      name.className = "primary-cell";
      name.textContent = event.event_title;
      const program = document.createElement("div");
      program.className = "secondary-cell";
      program.textContent = event.program_name;
      eventCell.append(name, program);
      tr.append(eventCell, cell(formatDate(event.event_date)));
      const statusCell = document.createElement("td");
      statusCell.append(badge(event.event_status));
      tr.append(statusCell, cell(formatNumber(event.valid_attendance), "numeric-cell"));
      tbody.append(tr);
    }
  } catch (error) {
    renderError(error, renderDashboard);
  }
}

async function renderPrograms() {
  renderLoading();
  try {
    const response = await apiRequest("/programs");
    const programs = response.data;
    root.innerHTML = `
      <section class="view-intro"><div><h2>Programs</h2><p id="program-count"></p></div></section>
      <div class="toolbar">
        <div class="field-group search-field"><label for="program-search">Search</label><input id="program-search" type="search" placeholder="Program or office" /></div>
        <div class="field-group"><label for="program-status">Status</label><select id="program-status"><option value="">All statuses</option><option value="active">Active</option><option value="archived">Archived</option></select></div>
      </div>
      <section class="panel"><div id="program-table" class="table-wrap"></div></section>`;
    setText("#program-count", `${formatNumber(programs.length)} visible program${programs.length === 1 ? "" : "s"}`);

    const draw = () => {
      const search = document.querySelector("#program-search").value.trim().toLowerCase();
      const status = document.querySelector("#program-status").value;
      const filtered = programs.filter((program) => {
        const haystack = `${program.program_name} ${program.owning_unit.unit_name}`.toLowerCase();
        return (!search || haystack.includes(search)) && (!status || program.program_status === status);
      });
      const container = document.querySelector("#program-table");
      if (!filtered.length) {
        renderEmpty(container, "No matching programs", "Adjust the current search or status filter.");
        return;
      }
      container.innerHTML = `<table class="data-table"><thead><tr><th>Program</th><th>Owning office/unit</th><th>Status</th></tr></thead><tbody></tbody></table>`;
      const tbody = container.querySelector("tbody");
      for (const program of filtered) {
        const tr = document.createElement("tr");
        tr.append(cell(program.program_name, "primary-cell"), cell(program.owning_unit.unit_name));
        const statusCell = document.createElement("td");
        statusCell.append(badge(program.program_status));
        tr.append(statusCell);
        tbody.append(tr);
      }
    };
    document.querySelector("#program-search").addEventListener("input", draw);
    document.querySelector("#program-status").addEventListener("change", draw);
    draw();
  } catch (error) {
    renderError(error, renderPrograms);
  }
}

async function renderEvents() {
  renderLoading();
  try {
    const response = await apiRequest("/events");
    const events = response.data;
    root.innerHTML = `
      <section class="view-intro"><div><h2>Events</h2><p id="event-count"></p></div></section>
      <div class="toolbar">
        <div class="field-group search-field"><label for="event-search">Search</label><input id="event-search" type="search" placeholder="Event, program, or venue" /></div>
        <div class="field-group"><label for="event-status">Status</label><select id="event-status"><option value="">All statuses</option><option value="draft">Draft</option><option value="open">Open</option><option value="closed">Closed</option></select></div>
      </div>
      <section class="panel"><div id="event-table" class="table-wrap"></div></section>`;
    setText("#event-count", `${formatNumber(events.length)} visible event${events.length === 1 ? "" : "s"}`);

    const draw = () => {
      const search = document.querySelector("#event-search").value.trim().toLowerCase();
      const status = document.querySelector("#event-status").value;
      const filtered = events.filter((event) => {
        const haystack = `${event.event_title} ${event.program.program_name} ${event.venue}`.toLowerCase();
        return (!search || haystack.includes(search)) && (!status || event.event_status === status);
      });
      const container = document.querySelector("#event-table");
      if (!filtered.length) {
        renderEmpty(container, "No matching events", "Adjust the current search or status filter.");
        return;
      }
      container.innerHTML = `<table class="data-table"><thead><tr><th>Event</th><th>Program</th><th>Date</th><th>Venue</th><th>Status</th></tr></thead><tbody></tbody></table>`;
      const tbody = container.querySelector("tbody");
      for (const event of filtered) {
        const tr = document.createElement("tr");
        tr.append(
          cell(event.event_title, "primary-cell"),
          cell(event.program.program_name),
          cell(formatDate(event.event_date)),
          cell(event.venue),
        );
        const statusCell = document.createElement("td");
        statusCell.append(badge(event.event_status));
        tr.append(statusCell);
        tbody.append(tr);
      }
    };
    document.querySelector("#event-search").addEventListener("input", draw);
    document.querySelector("#event-status").addEventListener("change", draw);
    draw();
  } catch (error) {
    renderError(error, renderEvents);
  }
}

function auditQuery() {
  const params = new URLSearchParams({ page: String(state.auditPage), pageSize: "25" });
  const fields = {
    "audit-search": "search",
    "audit-action": "action",
    "audit-entity": "entityType",
    "audit-date-from": "dateFrom",
    "audit-date-to": "dateTo",
  };
  for (const [id, key] of Object.entries(fields)) {
    const value = document.querySelector(`#${escapeSelector(id)}`)?.value.trim();
    if (value) params.set(key, value);
  }
  return params;
}

async function loadAuditTable() {
  const container = document.querySelector("#audit-results");
  container.innerHTML = `<div class="loading-state"><div class="large-spinner"></div><span>Loading audit logs...</span></div>`;
  try {
    const response = await apiRequest(`/audit-logs?${auditQuery()}`);
    const { items, pagination } = response.data;
    if (!items.length) {
      renderEmpty(container, "No audit logs found", "Adjust the filters or date range.");
      return;
    }
    container.innerHTML = `
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Date and time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Description</th></tr></thead><tbody></tbody></table></div>
      <div class="pagination-row"><span id="audit-page-info"></span><div class="pagination-actions"><button id="audit-prev" class="secondary-button" type="button" title="Previous page">←</button><button id="audit-next" class="secondary-button" type="button" title="Next page">→</button></div></div>`;
    const tbody = container.querySelector("tbody");
    for (const item of items) {
      const tr = document.createElement("tr");
      tr.append(
        cell(formatDateTime(item.created_at)),
        cell(item.actor?.full_name || "System"),
        cell(item.action.replaceAll("_", " "), "primary-cell"),
        cell(`${item.entity_type}${item.entity_id ? ` #${item.entity_id}` : ""}`),
        cell(item.description),
      );
      tbody.append(tr);
    }
    setText("#audit-page-info", `Page ${pagination.page} of ${Math.max(1, pagination.total_pages)} · ${formatNumber(pagination.total_items)} records`, container);
    const previous = container.querySelector("#audit-prev");
    const next = container.querySelector("#audit-next");
    previous.disabled = pagination.page <= 1;
    next.disabled = pagination.page >= pagination.total_pages;
    previous.addEventListener("click", () => {
      state.auditPage -= 1;
      loadAuditTable();
    });
    next.addEventListener("click", () => {
      state.auditPage += 1;
      loadAuditTable();
    });
  } catch (error) {
    renderEmpty(container, "Unable to load audit logs", error.message);
  }
}

async function renderAuditLogs() {
  if (state.user.role.role_name !== "super_admin") {
    navigate("dashboard");
    return;
  }
  root.innerHTML = `
    <section class="view-intro"><div><h2>Audit Logs</h2><p>System and administrator action history</p></div></section>
    <form id="audit-filters" class="toolbar">
      <div class="field-group search-field"><label for="audit-search">Search</label><input id="audit-search" type="search" maxlength="100" placeholder="Action, entity, actor" /></div>
      <div class="field-group"><label for="audit-action">Action</label><input id="audit-action" maxlength="100" placeholder="Exact action" /></div>
      <div class="field-group"><label for="audit-entity">Entity type</label><input id="audit-entity" maxlength="100" placeholder="e.g. event" /></div>
      <div class="field-group"><label for="audit-date-from">From</label><input id="audit-date-from" type="date" /></div>
      <div class="field-group"><label for="audit-date-to">To</label><input id="audit-date-to" type="date" /></div>
      <button class="primary-button" type="submit">Apply</button>
    </form>
    <section id="audit-results" class="panel"></section>`;
  document.querySelector("#audit-filters").addEventListener("submit", (event) => {
    event.preventDefault();
    state.auditPage = 1;
    loadAuditTable();
  });
  await loadAuditTable();
}

function closeSidebar() {
  sidebar.classList.remove("open");
  scrim.hidden = true;
}

function navigate(requestedView) {
  const config = views[requestedView] || views.dashboard;
  if (config.superAdminOnly && state.user.role.role_name !== "super_admin") {
    requestedView = "dashboard";
  }
  state.view = requestedView;
  window.location.hash = requestedView;
  pageTitle.textContent = views[requestedView].title;
  for (const item of document.querySelectorAll(".nav-item")) {
    item.classList.toggle("active", item.dataset.view === requestedView);
  }
  closeSidebar();
  root.focus({ preventScroll: true });
  views[requestedView].load();
}

function initializeUser(user) {
  state.user = user;
  setText("#sidebar-user-name", user.full_name);
  setText("#sidebar-user-role", formatRole(user.role.role_name));
  setText("#user-initials", initials(user.full_name));
  document.querySelector("#audit-nav").hidden = user.role.role_name !== "super_admin";
}

for (const item of document.querySelectorAll(".nav-item")) {
  item.addEventListener("click", () => navigate(item.dataset.view));
}
document.querySelector("#logout-button").addEventListener("click", logout);
document.querySelector("#menu-button").addEventListener("click", () => {
  sidebar.classList.add("open");
  scrim.hidden = false;
});
scrim.addEventListener("click", closeSidebar);
refreshButton.addEventListener("click", async () => {
  refreshButton.disabled = true;
  await views[state.view].load();
  refreshButton.disabled = false;
  showToast("View refreshed.");
});
window.addEventListener("hashchange", () => {
  const requested = window.location.hash.slice(1) || "dashboard";
  if (requested !== state.view) navigate(requested);
});

const user = await requireAdmin();
if (user) {
  initializeUser(user);
  appLoading.hidden = true;
  app.hidden = false;
  navigate(window.location.hash.slice(1) || "dashboard");
}
