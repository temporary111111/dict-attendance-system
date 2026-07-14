import { apiDownload, apiRequest, getApiOrigin } from "./api.js";
import { logout, requireAdmin } from "./auth.js";

const app = document.querySelector("#admin-app");
const appLoading = document.querySelector("#app-loading");
const root = document.querySelector("#view-root");
const pageTitle = document.querySelector("#page-title");
const refreshButton = document.querySelector("#refresh-button");
const sidebar = document.querySelector("#sidebar");
const scrim = document.querySelector("#sidebar-scrim");
const dialog = document.querySelector("#workspace-dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogContent = document.querySelector("#dialog-content");

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

function isSuperAdmin() {
  return state.user?.role.role_name === "super_admin";
}

function eventDateValue(value) {
  return value ? String(value).slice(0, 10) : "";
}

function setDialogError(message = "") {
  const target = dialogContent.querySelector("#dialog-error");
  if (target) target.textContent = message;
}

function openDialog(title, content) {
  dialogTitle.textContent = title;
  dialogContent.innerHTML = content;
  if (!dialog.open) dialog.showModal();
}

function closeDialog() {
  if (dialog.open) dialog.close();
}

function setButtonBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle("is-loading", busy);
}

async function downloadPdf(eventId, button) {
  setButtonBusy(button, true);
  try {
    const result = await apiDownload(`/events/${eventId}/attendance-sheet-exports`, {
      method: "POST",
    });
    const url = URL.createObjectURL(result.blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = result.filename || `attendance-sheet-event-${eventId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
    showToast("Attendance-sheet PDF generated.");
  } catch (error) {
    setDialogError(error.message);
  } finally {
    setButtonBusy(button, false);
  }
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
      <section class="view-intro"><div><h2>Programs</h2><p id="program-count"></p></div>${isSuperAdmin() ? '<button id="create-program" class="primary-button" type="button">Add program</button>' : ""}</section>
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
      container.innerHTML = `<table class="data-table"><thead><tr><th>Program</th><th>Owning office/unit</th><th>Status</th><th>Action</th></tr></thead><tbody></tbody></table>`;
      const tbody = container.querySelector("tbody");
      for (const program of filtered) {
        const tr = document.createElement("tr");
        tr.append(cell(program.program_name, "primary-cell"), cell(program.owning_unit.unit_name));
        const statusCell = document.createElement("td");
        statusCell.append(badge(program.program_status));
        tr.append(statusCell);
        const actionCell = document.createElement("td");
        const action = document.createElement("button");
        action.className = "table-button";
        action.type = "button";
        action.textContent = isSuperAdmin() ? "Manage" : "View";
        action.addEventListener("click", () => showProgramDialog(program));
        actionCell.append(action);
        tr.append(actionCell);
        tbody.append(tr);
      }
    };
    document.querySelector("#program-search").addEventListener("input", draw);
    document.querySelector("#program-status").addEventListener("change", draw);
    document.querySelector("#create-program")?.addEventListener("click", () => showProgramDialog());
    draw();
  } catch (error) {
    renderError(error, renderPrograms);
  }
}

async function showProgramDialog(program = null) {
  if (!isSuperAdmin()) {
    openDialog("Program", `<div class="dialog-stack"><div id="program-view-meta"></div></div>`);
    const meta = document.createElement("dl");
    meta.className = "event-meta";
    for (const [label, value] of [["Program", program.program_name], ["Owning unit", program.owning_unit.unit_name], ["Status", program.program_status]]) {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value;
      meta.append(dt, dd);
    }
    dialogContent.querySelector("#program-view-meta").append(meta);
    return;
  }

  openDialog(
    program ? "Manage program" : "Add program",
    `<form id="program-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="form-grid">
        <div class="field-group full-span"><label for="program-name">Program name</label><input id="program-name" name="program_name" maxlength="200" required /></div>
        <div class="field-group full-span"><label for="program-unit">Owning office or unit</label><select id="program-unit" name="owning_unit_id" required></select></div>
        <div class="field-group full-span"><label for="program-description">Description</label><textarea id="program-description" name="description" maxlength="5000"></textarea></div>
      </div>
      <div class="dialog-actions">${program ? `<button id="program-status-action" class="danger-button" type="button">${program.program_status === "active" ? "Archive program" : "Restore program"}</button>` : ""}<button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save program</span><span class="button-spinner"></span></button></div>
    </form>`,
  );
  const form = dialogContent.querySelector("#program-form");
  const unitSelect = form.elements.owning_unit_id;
  try {
    const units = (await apiRequest("/organizational-units")).data;
    for (const unit of units) {
      const option = document.createElement("option");
      option.value = unit.org_unit_id;
      option.textContent = unit.unit_name;
      unitSelect.append(option);
    }
    if (program) {
      form.elements.program_name.value = program.program_name;
      form.elements.owning_unit_id.value = String(program.owning_unit.org_unit_id);
      form.elements.description.value = program.description || "";
    }
  } catch (error) {
    setDialogError(error.message);
  }
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  dialogContent.querySelector("#program-status-action")?.addEventListener("click", async (clickEvent) => {
    const nextStatus = program.program_status === "active" ? "archived" : "active";
    if (!window.confirm(`${nextStatus === "archived" ? "Archive" : "Restore"} this program?`)) return;
    const button = clickEvent.currentTarget;
    setButtonBusy(button, true);
    setDialogError();
    try {
      await apiRequest(`/programs/${program.program_id}/archive`, { method: "PATCH", body: { program_status: nextStatus } });
      closeDialog();
      showToast("Program status updated.");
      renderPrograms();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(button, false);
    }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = form.querySelector('[type="submit"]');
    setButtonBusy(save, true);
    setDialogError();
    const payload = {
      program_name: form.elements.program_name.value,
      owning_unit_id: Number(form.elements.owning_unit_id.value),
      description: form.elements.description.value.trim() || null,
    };
    try {
      await apiRequest(program ? `/programs/${program.program_id}` : "/programs", {
        method: program ? "PATCH" : "POST",
        body: payload,
      });
      closeDialog();
      showToast(program ? "Program updated." : "Program created.");
      renderPrograms();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(save, false);
    }
  });
}

async function renderEvents() {
  renderLoading();
  try {
    const response = await apiRequest("/events");
    const events = response.data;
    root.innerHTML = `
      <section class="view-intro"><div><h2>Events</h2><p id="event-count"></p></div><button id="create-event" class="primary-button" type="button">Add event</button></section>
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
      container.innerHTML = `<table class="data-table"><thead><tr><th>Event</th><th>Program</th><th>Date</th><th>Venue</th><th>Status</th><th>Action</th></tr></thead><tbody></tbody></table>`;
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
        const actionCell = document.createElement("td");
        const action = document.createElement("button");
        action.className = "table-button";
        action.type = "button";
        action.textContent = "Manage";
        action.addEventListener("click", () => showEventDialog(event));
        actionCell.append(action);
        tr.append(actionCell);
        tbody.append(tr);
      }
    };
    document.querySelector("#event-search").addEventListener("input", draw);
    document.querySelector("#event-status").addEventListener("change", draw);
    document.querySelector("#create-event").addEventListener("click", () => showEventForm());
    draw();
  } catch (error) {
    renderError(error, renderEvents);
  }
}

async function showEventForm(event = null) {
  const programs = (await apiRequest("/programs")).data.filter((program) => program.program_status === "active");
  openDialog(
    event ? "Edit event" : "Add event",
    `<form id="event-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="form-grid">
        ${event ? "" : '<div class="field-group full-span"><label for="event-program">Program</label><select id="event-program" name="program_id" required></select></div>'}
        <div class="field-group full-span"><label for="event-title">Event title</label><input id="event-title" name="event_title" maxlength="200" required /></div>
        <div class="field-group"><label for="event-date">Event date</label><input id="event-date" name="event_date" type="date" required /></div>
        <div class="field-group"><label for="event-venue">Venue</label><input id="event-venue" name="venue" maxlength="255" required /></div>
        <div class="field-group full-span"><label for="event-description">Description</label><textarea id="event-description" name="event_description" maxlength="5000"></textarea></div>
      </div>
      <div class="dialog-actions"><button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save event</span><span class="button-spinner"></span></button></div>
    </form>`,
  );
  const form = dialogContent.querySelector("#event-form");
  if (!event) {
    const select = form.elements.program_id;
    for (const program of programs) {
      const option = document.createElement("option");
      option.value = program.program_id;
      option.textContent = program.program_name;
      select.append(option);
    }
  } else {
    form.elements.event_title.value = event.event_title;
    form.elements.event_date.value = eventDateValue(event.event_date);
    form.elements.venue.value = event.venue;
    form.elements.event_description.value = event.event_description || "";
  }
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  form.addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    const save = form.querySelector('[type="submit"]');
    setButtonBusy(save, true);
    setDialogError();
    const payload = {
      event_title: form.elements.event_title.value,
      event_date: form.elements.event_date.value,
      venue: form.elements.venue.value,
      event_description: form.elements.event_description.value.trim() || null,
    };
    try {
      const response = await apiRequest(event ? `/events/${event.event_id}` : `/programs/${form.elements.program_id.value}/events`, {
        method: event ? "PATCH" : "POST",
        body: payload,
      });
      showToast(event ? "Event updated." : "Event created.");
      await renderEvents();
      showEventDialog(response.data);
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(save, false);
    }
  });
}

function appendEventMeta(container, event) {
  const meta = document.createElement("dl");
  meta.className = "event-meta";
  const values = [
    ["Program", event.program.program_name],
    ["Date", formatDate(event.event_date)],
    ["Venue", event.venue],
    ["Status", event.event_status],
    ["Event code", event.event_code],
    ["Description", event.event_description || "-"],
  ];
  for (const [label, value] of values) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    meta.append(dt, dd);
  }
  container.append(meta);
}

async function showEventDialog(event) {
  const response = await apiRequest(`/events/${event.event_id}`);
  const current = response.data;
  openDialog("Manage event", `
    <div class="dialog-stack">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div id="event-meta"></div>
      <div class="event-actions" id="event-actions"></div>
      <div id="event-qr"></div>
    </div>`,
  );
  appendEventMeta(dialogContent.querySelector("#event-meta"), current);
  const actions = dialogContent.querySelector("#event-actions");
  const addAction = (label, handler, className = "secondary-button", disabled = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.disabled = disabled;
    button.addEventListener("click", () => handler(button));
    actions.append(button);
  };
  const editable = current.event_status !== "archived";
  addAction("Edit", () => showEventForm(current), "secondary-button", !editable);
  addAction("Fields", () => showFieldSettings(current), "secondary-button", !editable);
  addAction("Attendance", () => showAttendanceList(current));
  addAction("Generate PDF", (button) => downloadPdf(current.event_id, button));
  if (editable) addAction("Generate QR/link", (button) => runEventAction(current, "/attendance-link", "POST", button));
  if (current.event_status === "draft") addAction("Open attendance", (button) => runEventAction(current, "/open", "POST", button), "primary-button");
  if (current.event_status === "open") addAction("Close attendance", (button) => runEventAction(current, "/close", "POST", button), "primary-button");
  if (isSuperAdmin() && current.event_status === "closed") addAction("Archive event", (button) => runEventAction(current, "/archive", "PATCH", button), "danger-button");

  if (current.public_attendance_url && current.qr_code_path) {
    const preview = dialogContent.querySelector("#event-qr");
    preview.className = "qr-preview";
    const image = document.createElement("img");
    image.src = `${getApiOrigin()}${current.qr_code_path}`;
    image.alt = `QR code for ${current.event_title}`;
    const link = document.createElement("a");
    link.className = "link-value";
    link.href = current.public_attendance_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = current.public_attendance_url;
    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "secondary-button";
    copy.textContent = "Copy attendance link";
    copy.addEventListener("click", async () => {
      await navigator.clipboard.writeText(current.public_attendance_url);
      showToast("Attendance link copied.");
    });
    preview.append(image, link, copy);
  }
}

async function runEventAction(event, suffix, method, button) {
  if (suffix === "/archive" && !window.confirm("Archive this closed event?")) return;
  setButtonBusy(button, true);
  setDialogError();
  try {
    const response = await apiRequest(`/events/${event.event_id}${suffix}`, { method });
    showToast(response.message);
    await renderEvents();
    showEventDialog(response.data);
  } catch (error) {
    setDialogError(error.message);
  } finally {
    setButtonBusy(button, false);
  }
}

async function showFieldSettings(event) {
  openDialog("Attendance fields", `<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert"></p><p class="secondary-cell">Required fields are shown to attendees. Locked fields are always required.</p><form id="field-settings-form" class="dialog-form"><div id="field-settings-list" class="settings-list"></div><div class="dialog-actions"><button class="secondary-button" type="button" data-back>Back</button><button class="primary-button" type="submit" ${event.event_status === "closed" || event.event_status === "archived" ? "disabled" : ""}><span class="button-label">Save requirements</span><span class="button-spinner"></span></button></div></form></div>`);
  const list = dialogContent.querySelector("#field-settings-list");
  try {
    const settings = (await apiRequest(`/events/${event.event_id}/attendance-field-settings`)).data;
    for (const setting of settings) {
      const row = document.createElement("div");
      row.className = "setting-row";
      const label = document.createElement("label");
      label.htmlFor = `field-${setting.field_key}`;
      label.textContent = setting.field_label;
      const note = document.createElement("small");
      note.textContent = setting.is_admin_configurable ? "Configurable" : "Always required";
      label.append(note);
      const input = document.createElement("input");
      input.id = `field-${setting.field_key}`;
      input.type = "checkbox";
      input.checked = setting.is_required;
      input.disabled = !setting.is_admin_configurable || event.event_status === "closed" || event.event_status === "archived";
      input.dataset.fieldKey = setting.field_key;
      row.append(label, input);
      list.append(row);
    }
  } catch (error) {
    setDialogError(error.message);
  }
  dialogContent.querySelector("[data-back]").addEventListener("click", () => showEventDialog(event));
  dialogContent.querySelector("#field-settings-form").addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    const save = submitEvent.currentTarget.querySelector('[type="submit"]');
    const requirements = {};
    for (const input of list.querySelectorAll("input[data-field-key]:not(:disabled)")) requirements[input.dataset.fieldKey] = input.checked;
    if (!Object.keys(requirements).length) return;
    setButtonBusy(save, true);
    setDialogError();
    try {
      await apiRequest(`/events/${event.event_id}/attendance-field-settings`, { method: "PATCH", body: { requirements } });
      showToast("Attendance field requirements updated.");
      showFieldSettings(event);
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(save, false);
    }
  });
}

async function showAttendanceList(event, page = 1) {
  openDialog("Attendance records", `<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert"></p><div class="toolbar"><div class="field-group search-field"><label for="attendance-search">Search</label><input id="attendance-search" type="search" placeholder="Name or email" /></div><div class="field-group"><label for="attendance-status">Status</label><select id="attendance-status"><option value="">All statuses</option><option value="valid">Valid</option><option value="duplicate">Duplicate</option><option value="invalid">Invalid</option><option value="void">Void</option></select></div><button id="attendance-filter" class="primary-button" type="button">Apply</button></div><div id="attendance-results" class="table-wrap"></div><div class="dialog-actions"><button class="secondary-button" type="button" data-back>Back</button><button id="export-pdf" class="secondary-button" type="button">Generate PDF</button></div></div>`);
  const load = async (requestedPage = 1) => {
    const search = dialogContent.querySelector("#attendance-search").value.trim();
    const status = dialogContent.querySelector("#attendance-status").value;
    const params = new URLSearchParams({ page: String(requestedPage), pageSize: "25" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    const container = dialogContent.querySelector("#attendance-results");
    container.innerHTML = '<div class="loading-state"><div class="large-spinner"></div><span>Loading attendance...</span></div>';
    try {
      const { items, pagination } = (await apiRequest(`/events/${event.event_id}/attendance-records?${params}`)).data;
      if (!items.length) {
        renderEmpty(container, "No attendance records", "No matching attendee was found.");
        return;
      }
      container.innerHTML = '<table class="data-table"><thead><tr><th>Attendee</th><th>Affiliation</th><th>Status</th><th>Submitted</th><th>Action</th></tr></thead><tbody></tbody></table><div class="pagination-row"><span id="attendance-page-info"></span><div class="pagination-actions"><button id="attendance-prev" class="secondary-button" type="button">Previous</button><button id="attendance-next" class="secondary-button" type="button">Next</button></div></div>';
      const tbody = container.querySelector("tbody");
      for (const record of items) {
        const tr = document.createElement("tr");
        tr.append(cell(record.attendee_name, "primary-cell"), cell(record.affiliation), (() => { const td = document.createElement("td"); td.append(badge(record.attendance_status)); return td; })(), cell(formatDateTime(record.submitted_at)));
        const actionCell = document.createElement("td");
        const action = document.createElement("button");
        action.type = "button";
        action.className = "table-button";
        action.textContent = "Review";
        action.addEventListener("click", () => showAttendanceStatusDialog(record, event));
        actionCell.append(action);
        tr.append(actionCell);
        tbody.append(tr);
      }
      setText("#attendance-page-info", `Page ${pagination.page} of ${Math.max(1, pagination.total_pages)} · ${formatNumber(pagination.total_items)} records`, container);
      const previous = container.querySelector("#attendance-prev");
      const next = container.querySelector("#attendance-next");
      previous.disabled = pagination.page <= 1;
      next.disabled = pagination.page >= pagination.total_pages;
      previous.addEventListener("click", () => load(pagination.page - 1));
      next.addEventListener("click", () => load(pagination.page + 1));
    } catch (error) {
      setDialogError(error.message);
    }
  };
  dialogContent.querySelector("#attendance-filter").addEventListener("click", () => load(1));
  dialogContent.querySelector("[data-back]").addEventListener("click", () => showEventDialog(event));
  dialogContent.querySelector("#export-pdf").addEventListener("click", (clickEvent) => downloadPdf(event.event_id, clickEvent.currentTarget));
  await load(page);
}

async function showAttendanceStatusDialog(record, event) {
  const detail = (await apiRequest(`/attendance-records/${record.attendance_id}`)).data;
  openDialog("Review attendance record", `<form id="attendance-status-form" class="dialog-form"><p id="dialog-error" class="dialog-error" role="alert"></p><div id="attendance-detail"></div><div class="field-group"><label for="review-status">Attendance status</label><select id="review-status" name="attendance_status"><option value="valid">Valid</option><option value="duplicate">Duplicate</option><option value="invalid">Invalid</option><option value="void">Void</option></select></div><div class="field-group"><label for="review-reason">Reason for this update</label><textarea id="review-reason" name="reason" minlength="3" maxlength="300" required></textarea></div><div class="dialog-actions"><button class="secondary-button" type="button" data-back>Back</button><button class="primary-button" type="submit"><span class="button-label">Update status</span><span class="button-spinner"></span></button></div></form>`);
  const details = dialogContent.querySelector("#attendance-detail");
  const meta = document.createElement("dl");
  meta.className = "event-meta";
  for (const [label, value] of [["Attendee", `${detail.first_name} ${detail.middle_name || ""} ${detail.last_name} ${detail.suffix || ""}`.replace(/\s+/g, " ").trim()], ["Email", detail.email], ["Affiliation", detail.affiliation || "-"], ["Designation", detail.designation_category || "-"], ["Submitted", formatDateTime(detail.submitted_at)], ["Current status", detail.attendance_status]]) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value;
    meta.append(dt, dd);
  }
  details.append(meta);
  dialogContent.querySelector("#review-status").value = detail.attendance_status;
  dialogContent.querySelector("[data-back]").addEventListener("click", () => showAttendanceList(event));
  dialogContent.querySelector("#attendance-status-form").addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    const save = submitEvent.currentTarget.querySelector('[type="submit"]');
    setButtonBusy(save, true);
    try {
      await apiRequest(`/attendance-records/${record.attendance_id}/status`, { method: "PATCH", body: { attendance_status: submitEvent.currentTarget.elements.attendance_status.value, reason: submitEvent.currentTarget.elements.reason.value } });
      showToast("Attendance status updated.");
      showAttendanceList(event);
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(save, false);
    }
  });
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

document.querySelector("#dialog-close").addEventListener("click", closeDialog);
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) closeDialog();
});
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
