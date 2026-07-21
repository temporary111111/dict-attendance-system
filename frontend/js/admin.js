import { apiDownload, apiRequest, getApiOrigin } from "./api.js";
import { logout, requireAdmin } from "./auth.js";

const app = document.querySelector("#admin-app");
const appLoading = document.querySelector("#app-loading");
const root = document.querySelector("#view-root");
const pageTitle = document.querySelector("#page-title");
const refreshButton = document.querySelector("#refresh-button");
const menuButton = document.querySelector("#menu-button");
const sidebar = document.querySelector("#sidebar");
const scrim = document.querySelector("#sidebar-scrim");
const dialog = document.querySelector("#workspace-dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogContent = document.querySelector("#dialog-content");

const state = {
  user: null,
  view: "dashboard",
  auditPage: 1,
  psgc: {
    page: 1,
    search: "",
    level: "",
    status: "active",
    trail: [],
  },
};

const views = {
  dashboard: { title: "Dashboard", load: renderDashboard },
  programs: { title: "Programs", load: renderPrograms },
  events: { title: "Events", load: renderEvents },
  reports: { title: "Reports", load: renderReports },
  units: { title: "Organizational Units", load: renderUnits, superAdminOnly: true },
  users: { title: "Admin Users", load: renderUsers, superAdminOnly: true },
  psgc: { title: "PSGC Data", load: renderPsgcManagement, superAdminOnly: true },
  audit: { title: "Audit Logs", load: renderAuditLogs, superAdminOnly: true },
};

function escapeSelector(value) {
  return CSS.escape(String(value));
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = String(value ?? "");
  return element.innerHTML;
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

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.role = "status";
  toast.setAttribute("aria-live", "polite");
  toast.setAttribute("aria-atomic", "true");
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
  dialog.scrollTop = 0;
  window.requestAnimationFrame(() => {
    const target = dialogContent.querySelector(
      "[autofocus], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), button:not(:disabled)",
    );
    target?.focus();
  });
}

function closeDialog() {
  if (dialog.open) dialog.close();
}

function setButtonBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle("is-loading", busy);
  button.setAttribute("aria-busy", String(busy));
}

async function copyText(value) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("Copy is not supported by this browser.");
}

async function downloadQr(imageUrl, eventCode, button) {
  setButtonBusy(button, true);
  try {
    const response = await fetch(imageUrl);
    if (!response.ok) throw new Error("QR image could not be downloaded.");
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = `attendance-qr-${eventCode}.png`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast("QR code downloaded.");
  } catch (error) {
    setDialogError(error.message);
  } finally {
    setButtonBusy(button, false);
  }
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
    `<form id="program-form" class="dialog-form" enctype="multipart/form-data">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="form-grid">
        <div class="field-group full-span"><label for="program-name">Program name</label><input id="program-name" name="program_name" maxlength="200" required /></div>
        <div class="field-group full-span"><label for="program-unit">Owning office or unit</label><select id="program-unit" name="owning_unit_id" required></select></div>
        <div class="field-group full-span"><label for="program-description">Description</label><textarea id="program-description" name="description" maxlength="5000"></textarea></div>
        <div class="field-group full-span">
          <label for="program-logo">Program logo <span class="field-hint">(PNG or JPEG, max 2 MB)</span></label>
          <div class="logo-upload-area" id="logo-upload-area">
            <div class="logo-preview-wrap" id="logo-preview-wrap" hidden>
              <img id="logo-preview" class="logo-preview" src="" alt="Program logo preview" />
              <button id="remove-logo" class="logo-remove-button" type="button" aria-label="Remove logo" title="Remove logo">✕</button>
            </div>
            <label class="logo-upload-label" id="logo-upload-label" for="program-logo">
              <span class="logo-upload-icon" aria-hidden="true">⬆</span>
              <span id="logo-upload-text">Click to upload logo</span>
              <span class="logo-upload-hint">PNG or JPEG · max 2 MB</span>
            </label>
            <input id="program-logo" name="logo" type="file" accept="image/png,image/jpeg" class="logo-file-input" />
          </div>
        </div>
      </div>
      <div class="dialog-actions">${program ? `<button id="manage-program-admins" class="secondary-button" type="button">Program Admins</button><button id="program-status-action" class="danger-button" type="button">${program.program_status === "active" ? "Archive program" : "Restore program"}</button>` : ""}<button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save program</span><span class="button-spinner"></span></button></div>
    </form>`,
  );
  const form = dialogContent.querySelector("#program-form");
  const unitSelect = form.elements.owning_unit_id;
  const logoInput = form.querySelector("#program-logo");
  const logoPreviewWrap = form.querySelector("#logo-preview-wrap");
  const logoPreview = form.querySelector("#logo-preview");
  const logoUploadLabel = form.querySelector("#logo-upload-label");
  const logoUploadText = form.querySelector("#logo-upload-text");
  const removeLogoButton = form.querySelector("#remove-logo");

  // Tracks whether the user explicitly wants to remove the existing logo.
  let pendingRemoveLogo = false;

  function showLogoPreview(src, filename) {
    logoPreview.src = src;
    logoPreviewWrap.hidden = false;
    logoUploadLabel.hidden = true;
    logoUploadText.textContent = filename || "Logo selected";
  }

  function clearLogoPreview() {
    logoPreview.src = "";
    logoPreviewWrap.hidden = true;
    logoUploadLabel.hidden = false;
    logoUploadText.textContent = "Click to upload logo";
    logoInput.value = "";
    pendingRemoveLogo = false;
  }

  // Show existing logo preview when editing.
  if (program?.logo_url) {
    showLogoPreview(`${getApiOrigin()}${program.logo_url}`, "Current logo");
  }

  logoInput.addEventListener("change", () => {
    const file = logoInput.files[0];
    if (!file) return;
    pendingRemoveLogo = false;
    const url = URL.createObjectURL(file);
    showLogoPreview(url, file.name);
  });

  removeLogoButton.addEventListener("click", () => {
    clearLogoPreview();
    if (program?.logo_url) pendingRemoveLogo = true;
  });

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
  dialogContent.querySelector("#manage-program-admins")?.addEventListener("click", () => showProgramAdmins(program));
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
    // Always use FormData since the backend now accepts multipart/form-data.
    const formData = new FormData();
    formData.set("program_name", form.elements.program_name.value);
    formData.set("owning_unit_id", String(Number(form.elements.owning_unit_id.value)));
    const desc = form.elements.description.value.trim();
    if (desc) formData.set("description", desc);
    const logoFile = logoInput.files[0];
    if (logoFile) {
      formData.set("logo", logoFile);
    } else if (pendingRemoveLogo) {
      formData.set("remove_logo", "true");
    }
    try {
      await apiRequest(program ? `/programs/${program.program_id}` : "/programs", {
        method: program ? "PATCH" : "POST",
        body: formData,
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


async function showProgramAdmins(program) {
  openDialog("Program Admin assignments", `<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert"></p><form id="assignment-form" class="toolbar"><div class="field-group search-field"><label for="assignment-user">Program Admin</label><select id="assignment-user" name="user_id" required></select></div><button class="primary-button" type="submit">Assign</button></form><div id="assignment-results" class="table-wrap"></div><div class="dialog-actions"><button class="secondary-button" type="button" data-back>Back to program</button></div></div>`);
  const select = dialogContent.querySelector("#assignment-user");
  const result = dialogContent.querySelector("#assignment-results");
  const load = async () => {
    result.innerHTML = '<div class="loading-state"><div class="large-spinner"></div><span>Loading assignments...</span></div>';
    try {
      const [assignmentsResponse, usersResponse] = await Promise.all([apiRequest(`/programs/${program.program_id}/admins`), apiRequest("/users")]);
      const assignments = assignmentsResponse.data;
      const eligibleUsers = usersResponse.data.filter((user) => user.account_status === "active" && user.role.role_name === "program_admin");
      select.innerHTML = "";
      for (const user of eligibleUsers) {
        const option = document.createElement("option");
        option.value = user.user_id;
        option.textContent = `${user.full_name} (${user.email})`;
        select.append(option);
      }
      if (!assignments.length) {
        renderEmpty(result, "No Program Admin assignments", "Assign an active Program Admin account to this program.");
        return;
      }
      result.innerHTML = '<table class="data-table"><thead><tr><th>Program Admin</th><th>Email</th><th>Status</th><th>Assigned</th><th>Action</th></tr></thead><tbody></tbody></table>';
      const tbody = result.querySelector("tbody");
      for (const assignment of assignments) {
        const row = document.createElement("tr");
        const statusCell = document.createElement("td");
        statusCell.append(badge(assignment.assignment_status));
        const actionCell = document.createElement("td");
        if (assignment.assignment_status === "active") {
          const revoke = document.createElement("button");
          revoke.type = "button";
          revoke.className = "table-button";
          revoke.textContent = "Revoke";
          revoke.addEventListener("click", async () => {
            if (!window.confirm("Revoke this Program Admin assignment?")) return;
            revoke.disabled = true;
            try {
              await apiRequest(`/program-admin-assignments/${assignment.assignment_id}/revoke`, { method: "PATCH" });
              showToast("Program Admin assignment revoked.");
              load();
            } catch (error) {
              setDialogError(error.message);
              revoke.disabled = false;
            }
          });
          actionCell.append(revoke);
        } else {
          actionCell.textContent = "-";
        }
        row.append(cell(assignment.user.full_name, "primary-cell"), cell(assignment.user.email), statusCell, cell(formatDateTime(assignment.assigned_at)), actionCell);
        tbody.append(row);
      }
    } catch (error) {
      setDialogError(error.message);
      renderEmpty(result, "Unable to load assignments", error.message);
    }
  };
  dialogContent.querySelector("[data-back]").addEventListener("click", () => showProgramDialog(program));
  dialogContent.querySelector("#assignment-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = event.currentTarget.querySelector('[type="submit"]');
    setButtonBusy(submit, true);
    setDialogError();
    try {
      await apiRequest(`/programs/${program.program_id}/admins`, { method: "POST", body: { user_id: Number(select.value) } });
      showToast("Program Admin assigned.");
      load();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(submit, false);
    }
  });
  await load();
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
  if (current.event_status === "closed") addAction("Reopen attendance", (button) => runEventAction(current, "/open", "POST", button), "primary-button");
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
      try {
        await copyText(current.public_attendance_url);
        showToast("Attendance link copied.");
      } catch (error) {
        setDialogError(error.message);
      }
    });
    const download = document.createElement("button");
    download.type = "button";
    download.className = "secondary-button";
    download.textContent = "Download QR";
    download.addEventListener("click", () => downloadQr(image.src, current.event_code, download));
    const qrActions = document.createElement("div");
    qrActions.className = "qr-actions";
    qrActions.append(copy, download);
    preview.append(image, link, qrActions);
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
  openDialog("Attendance fields", `<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert"></p><p class="secondary-cell">Choose which fixed fields attendees can see and which visible fields they must answer. Core identity and database-consent fields stay locked.</p><form id="field-settings-form" class="dialog-form"><div class="settings-heading"><span>Field</span><span>Show</span><span>Require</span></div><div id="field-settings-list" class="settings-list"></div><div class="dialog-actions"><button class="secondary-button" type="button" data-back>Back</button><button class="primary-button" type="submit" ${event.event_status === "closed" || event.event_status === "archived" ? "disabled" : ""}><span class="button-label">Save field settings</span><span class="button-spinner"></span></button></div></form></div>`);
  const list = dialogContent.querySelector("#field-settings-list");
  try {
    const settings = (await apiRequest(`/events/${event.event_id}/attendance-field-settings`)).data;
    for (const setting of settings) {
      const row = document.createElement("div");
      row.className = "setting-row";
      const label = document.createElement("label");
      label.textContent = setting.field_label;
      const note = document.createElement("small");
      note.textContent = setting.is_admin_configurable ? "Configurable" : "Always required";
      label.append(note);
      const locked = !setting.is_admin_configurable || event.event_status === "closed" || event.event_status === "archived";
      const visible = document.createElement("input");
      visible.type = "checkbox";
      visible.checked = setting.is_visible;
      visible.disabled = locked;
      visible.dataset.fieldKey = setting.field_key;
      visible.dataset.settingType = "visibility";
      visible.dataset.configurable = String(setting.is_admin_configurable);
      visible.setAttribute("aria-label", `Show ${setting.field_label}`);
      const required = document.createElement("input");
      required.type = "checkbox";
      required.checked = setting.is_required;
      required.disabled = locked || !setting.is_visible;
      required.dataset.fieldKey = setting.field_key;
      required.dataset.settingType = "requirement";
      required.dataset.configurable = String(setting.is_admin_configurable);
      required.setAttribute("aria-label", `Require ${setting.field_label}`);
      visible.addEventListener("change", () => {
        if (!visible.checked) required.checked = false;
        required.disabled = locked || !visible.checked;
        if (setting.field_key === "psgc_address" && !visible.checked) {
          for (const childKey of ["street_address", "postal_code"]) {
            const childVisible = list.querySelector(`[data-setting-type="visibility"][data-field-key="${childKey}"]`);
            if (childVisible) {
              childVisible.checked = false;
              childVisible.dispatchEvent(new Event("change"));
            }
          }
        }
      });
      row.append(label, visible, required);
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
    const visibility = {};
    for (const input of list.querySelectorAll("input[data-field-key]")) {
      if (input.dataset.configurable !== "true") continue;
      if (input.dataset.settingType === "visibility") visibility[input.dataset.fieldKey] = input.checked;
      if (input.dataset.settingType === "requirement") requirements[input.dataset.fieldKey] = input.checked;
    }
    setButtonBusy(save, true);
    setDialogError();
    try {
      await apiRequest(`/events/${event.event_id}/attendance-field-settings`, { method: "PATCH", body: { requirements, visibility } });
      showToast("Attendance field settings updated.");
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

async function renderReports() {
  renderLoading();
  try {
    const programs = (await apiRequest("/programs")).data;
    root.innerHTML = `
      <section class="view-intro"><div><h2>Attendance Reports</h2><p>Program and event attendance summaries</p></div></section>
      <form id="report-filters" class="toolbar">
        <div class="field-group search-field"><label for="report-program">Program</label><select id="report-program" required></select></div>
        <div class="field-group"><label for="report-date-from">From</label><input id="report-date-from" type="date" /></div>
        <div class="field-group"><label for="report-date-to">To</label><input id="report-date-to" type="date" /></div>
        <button class="primary-button" type="submit">Apply</button>
      </form>
      <section id="report-results"></section>`;
    const select = document.querySelector("#report-program");
    if (!programs.length) {
      renderEmpty(document.querySelector("#report-results"), "No visible programs", "Reports appear once you can access a program.");
      return;
    }
    for (const program of programs) {
      const option = document.createElement("option");
      option.value = program.program_id;
      option.textContent = program.program_name;
      select.append(option);
    }
    const load = () => loadProgramReport(Number(select.value));
    document.querySelector("#report-filters").addEventListener("submit", (event) => {
      event.preventDefault();
      load();
    });
    await load();
  } catch (error) {
    renderError(error, renderReports);
  }
}

async function loadProgramReport(programId) {
  const container = document.querySelector("#report-results");
  container.innerHTML = '<div class="panel loading-state"><div class="large-spinner"></div><span>Loading report...</span></div>';
  const params = new URLSearchParams();
  const dateFrom = document.querySelector("#report-date-from").value;
  const dateTo = document.querySelector("#report-date-to").value;
  if (dateFrom) params.set("dateFrom", dateFrom);
  if (dateTo) params.set("dateTo", dateTo);
  try {
    const data = (await apiRequest(`/reports/programs/${programId}/summary${params.size ? `?${params}` : ""}`)).data;
    container.innerHTML = `
      <section class="summary-grid" aria-label="Program report totals">
        <article class="summary-card"><span class="summary-label">Events</span><strong id="report-total-events" class="summary-value"></strong></article>
        <article class="summary-card green"><span class="summary-label">Attendance records</span><strong id="report-total-attendance" class="summary-value"></strong></article>
        <article class="summary-card amber"><span class="summary-label">Valid attendees</span><strong id="report-valid-attendance" class="summary-value"></strong></article>
      </section>
      <section class="dashboard-grid">
        <article class="panel"><header class="panel-header"><h3>Attendance status</h3></header><div id="report-attendance-bars" class="panel-body status-bars"></div></article>
        <article class="panel"><header class="panel-header"><h3>Event status</h3></header><div id="report-event-bars" class="panel-body status-bars"></div></article>
      </section>
      <section class="panel report-events-panel"><header class="panel-header"><h3 id="report-event-heading"></h3></header><div id="report-event-table" class="table-wrap"></div></section>`;
    setText("#report-total-events", formatNumber(data.total_events));
    setText("#report-total-attendance", formatNumber(data.total_attendance));
    setText("#report-valid-attendance", formatNumber(data.attendance_by_status.valid));
    setText("#report-event-heading", `${data.program_name} events`);
    statusBars(document.querySelector("#report-attendance-bars"), data.attendance_by_status);
    statusBars(document.querySelector("#report-event-bars"), data.events_by_status);
    const events = document.querySelector("#report-event-table");
    if (!data.events.length) {
      renderEmpty(events, "No events in this date range", "Adjust the selected dates or choose another program.");
      return;
    }
    events.innerHTML = '<table class="data-table"><thead><tr><th>Event</th><th>Date</th><th>Status</th><th class="numeric-cell">Attendance</th><th class="numeric-cell">Valid</th><th>Action</th></tr></thead><tbody></tbody></table>';
    const tbody = events.querySelector("tbody");
    for (const event of data.events) {
      const row = document.createElement("tr");
      const statusCell = document.createElement("td");
      statusCell.append(badge(event.event_status));
      const actionCell = document.createElement("td");
      const action = document.createElement("button");
      action.type = "button";
      action.className = "table-button";
      action.textContent = "View summary";
      action.addEventListener("click", () => showEventReport(event.event_id));
      actionCell.append(action);
      row.append(cell(event.event_title, "primary-cell"), cell(formatDate(event.event_date)), statusCell, cell(formatNumber(event.total_attendance), "numeric-cell"), cell(formatNumber(event.valid_attendance), "numeric-cell"), actionCell);
      tbody.append(row);
    }
  } catch (error) {
    container.innerHTML = '<section class="panel error-state"><div class="state-symbol">!</div><strong>Unable to load this report</strong><span id="report-error-message"></span></section>';
    setText("#report-error-message", error.message, container);
  }
}

async function showEventReport(eventId) {
  openDialog("Event attendance summary", '<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert"></p><div id="event-report-content" class="loading-state"><div class="large-spinner"></div><span>Loading event summary...</span></div></div>');
  const container = dialogContent.querySelector("#event-report-content");
  try {
    const data = (await apiRequest(`/reports/events/${eventId}/attendance`)).data;
    container.className = "dialog-stack";
    container.innerHTML = '<section class="summary-grid"><article class="summary-card"><span class="summary-label">Attendance records</span><strong id="event-report-total" class="summary-value"></strong></article><article class="summary-card green"><span class="summary-label">Valid attendees</span><strong id="event-report-valid" class="summary-value"></strong></article><article class="summary-card amber"><span class="summary-label">Documentation consent</span><strong id="event-report-consent" class="summary-value"></strong></article></section><dl id="event-report-meta" class="event-meta"></dl><section class="panel"><header class="panel-header"><h3>Attendance status</h3></header><div id="event-report-statuses" class="panel-body status-bars"></div></section><section class="panel"><header class="panel-header"><h3>Attendees by sex</h3></header><div id="event-report-sex" class="panel-body status-bars"></div></section><div class="dialog-actions"><button id="event-report-pdf" class="secondary-button" type="button">Generate PDF</button><button class="primary-button" type="button" data-close>Close</button></div>';
    setText("#event-report-total", formatNumber(data.total_attendance), container);
    setText("#event-report-valid", formatNumber(data.attendance_by_status.valid), container);
    setText("#event-report-consent", `${formatNumber(data.documentation_consent.accepted)} accepted`, container);
    const meta = container.querySelector("#event-report-meta");
    for (const [label, value] of [["Program", data.program_name], ["Event", data.event_title], ["Date", formatDate(data.event_date)], ["Venue", data.venue], ["Status", data.event_status]]) {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value;
      meta.append(dt, dd);
    }
    statusBars(container.querySelector("#event-report-statuses"), data.attendance_by_status);
    statusBars(container.querySelector("#event-report-sex"), data.attendees_by_sex);
    container.querySelector("[data-close]").addEventListener("click", closeDialog);
    container.querySelector("#event-report-pdf").addEventListener("click", (event) => downloadPdf(eventId, event.currentTarget));
  } catch (error) {
    container.className = "error-state";
    container.textContent = error.message;
  }
}

async function renderUnits() {
  renderLoading();
  try {
    const units = (await apiRequest("/organizational-units")).data;
    const unitsById = new Map(units.map((unit) => [unit.org_unit_id, unit]));
    root.innerHTML = `
      <section class="view-intro"><div><h2>Organizational Units</h2><p id="unit-count"></p></div><button id="create-unit" class="primary-button" type="button">Add unit</button></section>
      <div class="toolbar"><div class="field-group search-field"><label for="unit-search">Search</label><input id="unit-search" type="search" placeholder="Unit name, type, or code" /></div><div class="field-group"><label for="unit-status">Status</label><select id="unit-status"><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></div></div>
      <section class="panel"><div id="unit-table" class="table-wrap"></div></section>`;
    setText("#unit-count", `${formatNumber(units.length)} organizational unit${units.length === 1 ? "" : "s"}`);
    const draw = () => {
      const search = document.querySelector("#unit-search").value.trim().toLowerCase();
      const status = document.querySelector("#unit-status").value;
      const filtered = units.filter((unit) => {
        const matchesSearch = `${unit.unit_name} ${unit.unit_type} ${unit.unit_code || ""}`.toLowerCase().includes(search);
        const unitStatus = unit.is_active ? "active" : "inactive";
        return matchesSearch && (!status || status === unitStatus);
      });
      const container = document.querySelector("#unit-table");
      if (!filtered.length) {
        renderEmpty(container, "No matching units", "Adjust the current search.");
        return;
      }
      container.innerHTML = '<table class="data-table"><thead><tr><th>Unit</th><th>Type</th><th>Code</th><th>Parent unit</th><th>Status</th><th>Action</th></tr></thead><tbody></tbody></table>';
      const tbody = container.querySelector("tbody");
      for (const unit of filtered) {
        const row = document.createElement("tr");
        row.append(cell(unit.unit_name, "primary-cell"), cell(unit.unit_type), cell(unit.unit_code), cell(unitsById.get(unit.parent_unit_id)?.unit_name || "Root unit"));
        const statusCell = document.createElement("td");
        statusCell.append(badge(unit.is_active ? "active" : "inactive"));
        row.append(statusCell);
        const actionCell = document.createElement("td");
        const action = document.createElement("button");
        action.type = "button";
        action.className = "table-button";
        action.textContent = "Manage";
        action.addEventListener("click", () => showUnitDialog(unit, units));
        actionCell.append(action);
        row.append(actionCell);
        tbody.append(row);
      }
    };
    document.querySelector("#unit-search").addEventListener("input", draw);
    document.querySelector("#unit-status").addEventListener("change", draw);
    document.querySelector("#create-unit").addEventListener("click", () => showUnitDialog(null, units));
    draw();
  } catch (error) {
    renderError(error, renderUnits);
  }
}

function addUnitOptions(select, units, selectedId = null, excludeId = null) {
  const rootOption = document.createElement("option");
  rootOption.value = "";
  rootOption.textContent = "No parent (root unit)";
  select.append(rootOption);
  for (const unit of units) {
    if (unit.org_unit_id === excludeId || !unit.is_active) continue;
    const option = document.createElement("option");
    option.value = unit.org_unit_id;
    option.textContent = `${unit.unit_name} (${unit.unit_type})`;
    select.append(option);
  }
  select.value = selectedId ? String(selectedId) : "";
}

function showUnitDialog(unit, units) {
  openDialog(unit ? "Manage organizational unit" : "Add organizational unit", `
    <form id="unit-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="form-grid">
        <div class="field-group full-span"><label for="unit-name">Unit name</label><input id="unit-name" name="unit_name" maxlength="200" required /></div>
        <div class="field-group"><label for="unit-type">Unit type</label><input id="unit-type" name="unit_type" maxlength="50" placeholder="office, division, section" required /></div>
        <div class="field-group"><label for="unit-code">Unit code</label><input id="unit-code" name="unit_code" maxlength="50" /></div>
        <div class="field-group full-span"><label for="unit-parent">Parent unit</label><select id="unit-parent" name="parent_unit_id"></select></div>
      </div>
      <div class="dialog-actions">${unit ? `<button id="unit-status-action" class="${unit.is_active ? "danger-button" : "secondary-button"}" type="button">${unit.is_active ? "Deactivate unit" : "Restore unit"}</button>` : ""}<button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save unit</span><span class="button-spinner"></span></button></div>
    </form>`);
  const form = dialogContent.querySelector("#unit-form");
  addUnitOptions(form.elements.parent_unit_id, units, unit?.parent_unit_id, unit?.org_unit_id);
  if (unit) {
    form.elements.unit_name.value = unit.unit_name;
    form.elements.unit_type.value = unit.unit_type;
    form.elements.unit_code.value = unit.unit_code || "";
  }
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  dialogContent.querySelector("#unit-status-action")?.addEventListener("click", async (clickEvent) => {
    const nextActive = !unit.is_active;
    const verb = nextActive ? "Restore" : "Deactivate";
    if (!window.confirm(`${verb} this organizational unit?`)) return;
    const button = clickEvent.currentTarget;
    setButtonBusy(button, true);
    setDialogError();
    try {
      await apiRequest(`/organizational-units/${unit.org_unit_id}`, { method: "PATCH", body: { is_active: nextActive } });
      closeDialog();
      showToast(`Organizational unit ${nextActive ? "restored" : "deactivated"}.`);
      renderUnits();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(button, false);
    }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = form.querySelector('[type="submit"]');
    const payload = {
      unit_name: form.elements.unit_name.value,
      unit_type: form.elements.unit_type.value,
      unit_code: form.elements.unit_code.value.trim() || null,
      parent_unit_id: form.elements.parent_unit_id.value ? Number(form.elements.parent_unit_id.value) : null,
    };
    setButtonBusy(save, true);
    setDialogError();
    try {
      await apiRequest(unit ? `/organizational-units/${unit.org_unit_id}` : "/organizational-units", { method: unit ? "PATCH" : "POST", body: payload });
      closeDialog();
      showToast(unit ? "Organizational unit updated." : "Organizational unit created.");
      renderUnits();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(save, false);
    }
  });
}

const PSGC_LEVEL_LABELS = {
  region: "Region",
  province: "Province",
  city_municipality: "City / municipality",
  barangay: "Barangay",
};

function psgcLevelLabel(level) {
  return PSGC_LEVEL_LABELS[level] || "PSGC location";
}

function psgcChildrenPath(item) {
  if (item.level === "region") return `/admin/psgc/regions/${encodeURIComponent(item.code)}/children`;
  if (item.level === "province") return `/admin/psgc/provinces/${encodeURIComponent(item.code)}/children`;
  return `/admin/psgc/cities-municipalities/${encodeURIComponent(item.code)}/children`;
}

function psgcDetailPath(item) {
  return `/admin/psgc/${item.level}/${encodeURIComponent(item.code)}`;
}

function psgcErrorMessage(error) {
  if (error.code !== "PSGC_RECORD_IN_USE") return error.message;
  const childCount = Number(error.fields?.child_count || 0);
  const addressCount = Number(error.fields?.attendance_address_reference_count || 0);
  return `${error.message} Child locations: ${childCount}. Attendance address records: ${addressCount}.`;
}

function psgcBreadcrumbMarkup() {
  const crumbs = [{ label: "Regions", index: -1 }, ...state.psgc.trail.map((item, index) => ({ label: item.name, index }))];
  return crumbs.map((crumb, index) => `${index ? '<span class="psgc-breadcrumb-separator" aria-hidden="true">/</span>' : ""}<button class="psgc-breadcrumb-button" type="button" data-psgc-trail-index="${crumb.index}">${escapeHtml(crumb.label)}</button>`).join("");
}

async function loadPsgcWorkspace() {
  const workspace = state.psgc;
  const query = new URLSearchParams({
    page: String(workspace.page),
    pageSize: "25",
    status: workspace.status,
  });
  if (workspace.search) {
    query.set("query", workspace.search);
    if (workspace.level) query.set("level", workspace.level);
    return (await apiRequest(`/admin/psgc/search?${query}`)).data;
  }
  const current = workspace.trail.at(-1);
  if (!current) return (await apiRequest(`/admin/psgc/regions?${query}`)).data;
  return (await apiRequest(`${psgcChildrenPath(current)}?${query}`)).data;
}

function renderPsgcPagination(container, pagination) {
  if (!pagination.total_items) return;
  const row = document.createElement("div");
  row.className = "pagination-row";
  const label = document.createElement("span");
  label.textContent = `Page ${pagination.page} of ${pagination.total_pages} | ${formatNumber(pagination.total_items)} record${pagination.total_items === 1 ? "" : "s"}`;
  const actions = document.createElement("div");
  actions.className = "pagination-actions";
  const previous = document.createElement("button");
  previous.className = "secondary-button";
  previous.type = "button";
  previous.textContent = "Previous";
  previous.disabled = pagination.page <= 1;
  previous.addEventListener("click", () => {
    state.psgc.page = pagination.page - 1;
    renderPsgcManagement();
  });
  const next = document.createElement("button");
  next.className = "secondary-button";
  next.type = "button";
  next.textContent = "Next";
  next.disabled = pagination.page >= pagination.total_pages;
  next.addEventListener("click", () => {
    state.psgc.page = pagination.page + 1;
    renderPsgcManagement();
  });
  actions.append(previous, next);
  row.append(label, actions);
  container.append(row);
}

async function browsePsgcRecord(item) {
  if (item.level === "barangay") return;
  state.psgc.search = "";
  state.psgc.page = 1;
  const detail = (await apiRequest(psgcDetailPath(item))).data;
  state.psgc.trail = detail.path;
  await renderPsgcManagement();
}

function renderPsgcWorkspaceTable(container, data, isSearch) {
  const items = data.items || [];
  if (!items.length) {
    renderEmpty(
      container,
      "No PSGC records found",
      isSearch ? "Try a different code, name, level, or status." : "There are no matching locations at this level.",
    );
    return;
  }
  container.innerHTML = '<table class="data-table"><thead><tr><th>Location</th><th>Level</th><th>PSGC code</th><th>Parent / path</th><th>Status</th><th>Action</th></tr></thead><tbody></tbody></table>';
  const tbody = container.querySelector("tbody");
  for (const item of items) {
    const tr = document.createElement("tr");
    const locationCell = document.createElement("td");
    const name = document.createElement("div");
    name.className = "primary-cell";
    name.textContent = item.name;
    locationCell.append(name);
    if (item.city_municipality_type) {
      const type = document.createElement("div");
      type.className = "secondary-cell";
      type.textContent = item.city_municipality_type;
      locationCell.append(type);
    }
    tr.append(locationCell, cell(psgcLevelLabel(item.level)), cell(item.code, "psgc-code-cell"));
    tr.append(cell(item.path_label || item.parent_label || "-", "secondary-cell"));
    const statusCell = document.createElement("td");
    statusCell.append(badge(item.is_active ? "active" : "inactive"));
    tr.append(statusCell);
    const actionCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "psgc-table-actions";
    if (item.level !== "barangay") {
      const browse = document.createElement("button");
      browse.className = "table-button";
      browse.type = "button";
      browse.textContent = "Browse";
      browse.addEventListener("click", () => browsePsgcRecord(item).catch((error) => showToast(psgcErrorMessage(error))));
      actions.append(browse);
    }
    const details = document.createElement("button");
    details.className = "table-button";
    details.type = "button";
    details.textContent = "Details";
    details.addEventListener("click", () => showPsgcRecordDialog(item));
    actions.append(details);
    actionCell.append(actions);
    tr.append(actionCell);
    tbody.append(tr);
  }
  renderPsgcPagination(container.parentElement, data.pagination);
}

async function showPsgcRecordDialog(item) {
  openDialog("PSGC record", '<div class="dialog-stack"><div class="loading-state" role="status"><div class="large-spinner"></div><span>Loading record...</span></div></div>');
  try {
    const detail = (await apiRequest(psgcDetailPath(item))).data;
    const dependencies = detail.dependencies;
    const canChangeCodeOrDelete = !dependencies.child_count && !dependencies.attendance_address_reference_count;
    const path = detail.path.map((segment) => escapeHtml(segment.name)).join(" / ");
    const dependencyMessage = canChangeCodeOrDelete
      ? "No child location or attendance-address dependency."
      : `Child locations: ${formatNumber(dependencies.child_count)}. Attendance address records: ${formatNumber(dependencies.attendance_address_reference_count)}.`;
    openDialog(`${psgcLevelLabel(detail.level)} details`, `
      <div class="dialog-stack">
        <p id="dialog-error" class="dialog-error" role="alert"></p>
        <dl class="psgc-detail-list">
          <dt>Name</dt><dd>${escapeHtml(detail.name)}</dd>
          <dt>PSGC code</dt><dd class="psgc-code-cell">${escapeHtml(detail.code)}</dd>
          <dt>Level</dt><dd>${escapeHtml(psgcLevelLabel(detail.level))}</dd>
          <dt>Hierarchy</dt><dd>${path}</dd>
          <dt>Status</dt><dd>${detail.is_active ? "Active" : "Inactive"}</dd>
          <dt>Dependencies</dt><dd>${dependencyMessage}</dd>
        </dl>
        <div class="dialog-actions">
          ${detail.level !== "barangay" ? '<button id="psgc-browse-children" class="secondary-button" type="button">Browse children</button>' : ""}
          <button id="psgc-name-action" class="secondary-button" type="button">Correct name</button>
          <button id="psgc-status-action" class="${detail.is_active ? "danger-button" : "secondary-button"}" type="button">${detail.is_active ? "Deactivate" : "Restore"}</button>
          <button id="psgc-code-action" class="secondary-button" type="button" ${canChangeCodeOrDelete ? "" : "disabled"}>Correct code</button>
          <button id="psgc-delete-action" class="danger-button" type="button" ${canChangeCodeOrDelete ? "" : "disabled"}>Delete permanently</button>
          <button class="secondary-button" type="button" data-close>Close</button>
        </div>
      </div>`);
    dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
    dialogContent.querySelector("#psgc-browse-children")?.addEventListener("click", () => browsePsgcRecord(detail).catch((error) => setDialogError(psgcErrorMessage(error))));
    dialogContent.querySelector("#psgc-name-action").addEventListener("click", () => showPsgcNameDialog(detail));
    dialogContent.querySelector("#psgc-status-action").addEventListener("click", () => showPsgcStatusDialog(detail));
    dialogContent.querySelector("#psgc-code-action")?.addEventListener("click", () => showPsgcCodeDialog(detail));
    dialogContent.querySelector("#psgc-delete-action")?.addEventListener("click", () => showPsgcDeleteDialog(detail));
  } catch (error) {
    openDialog("PSGC record", `<div class="dialog-stack"><p id="dialog-error" class="dialog-error" role="alert">${escapeHtml(psgcErrorMessage(error))}</p><div class="dialog-actions"><button class="secondary-button" type="button" data-close>Close</button></div></div>`);
    dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  }
}

function bindPsgcMutation(form, endpoint, payloadFromForm, successMessage) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector('[type="submit"]');
    setButtonBusy(submit, true);
    setDialogError();
    try {
      await apiRequest(endpoint, { method: "PATCH", body: payloadFromForm() });
      closeDialog();
      showToast(successMessage);
      await renderPsgcManagement();
    } catch (error) {
      setDialogError(psgcErrorMessage(error));
    } finally {
      setButtonBusy(submit, false);
    }
  });
}

function showPsgcNameDialog(detail) {
  openDialog("Correct PSGC name", `
    <form id="psgc-name-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="field-group"><label for="psgc-corrected-name">Verified name</label><input id="psgc-corrected-name" name="name" maxlength="150" required value="${escapeHtml(detail.name)}" /></div>
      <div class="field-group"><label for="psgc-name-reason">Reason</label><textarea id="psgc-name-reason" name="reason" minlength="3" maxlength="500" required></textarea></div>
      <div class="dialog-actions"><button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save name</span><span class="button-spinner"></span></button></div>
    </form>`);
  const form = dialogContent.querySelector("#psgc-name-form");
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  bindPsgcMutation(form, `${psgcDetailPath(detail)}/name`, () => ({ name: form.elements.name.value, reason: form.elements.reason.value }), "PSGC name updated.");
}

function showPsgcStatusDialog(detail) {
  const nextActive = !detail.is_active;
  openDialog(`${nextActive ? "Restore" : "Deactivate"} PSGC record`, `
    <form id="psgc-status-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="field-group"><label for="psgc-status-reason">Reason</label><textarea id="psgc-status-reason" name="reason" minlength="3" maxlength="500" required></textarea></div>
      <div class="dialog-actions"><button class="secondary-button" type="button" data-close>Cancel</button><button class="${nextActive ? "primary-button" : "danger-button"}" type="submit"><span class="button-label">${nextActive ? "Restore record" : "Deactivate record"}</span><span class="button-spinner"></span></button></div>
    </form>`);
  const form = dialogContent.querySelector("#psgc-status-form");
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  bindPsgcMutation(form, `${psgcDetailPath(detail)}/status`, () => ({ is_active: nextActive, reason: form.elements.reason.value }), `PSGC record ${nextActive ? "restored" : "deactivated"}.`);
}

function showPsgcCodeDialog(detail) {
  openDialog("Correct PSGC code", `
    <form id="psgc-code-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <div class="field-group"><label for="psgc-new-code">Verified 10-digit code</label><input id="psgc-new-code" name="new_code" inputmode="numeric" pattern="[0-9]{10}" minlength="10" maxlength="10" required /></div>
      <div class="field-group"><label for="psgc-code-reason">Reason</label><textarea id="psgc-code-reason" name="reason" minlength="3" maxlength="500" required></textarea></div>
      <label class="checkbox-field"><input name="confirmed" type="checkbox" required /> I verified that this row has no child location or attendance-address dependency.</label>
      <div class="dialog-actions"><button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save code</span><span class="button-spinner"></span></button></div>
    </form>`);
  const form = dialogContent.querySelector("#psgc-code-form");
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  bindPsgcMutation(form, `${psgcDetailPath(detail)}/code`, () => ({ new_code: form.elements.new_code.value, reason: form.elements.reason.value, confirmed: form.elements.confirmed.checked }), "PSGC code updated.");
}

function showPsgcDeleteDialog(detail) {
  openDialog("Delete PSGC record permanently", `
    <form id="psgc-delete-form" class="dialog-form">
      <p id="dialog-error" class="dialog-error" role="alert"></p>
      <p class="psgc-warning">This removes ${escapeHtml(detail.name)} from the local PSGC lookup data.</p>
      <div class="field-group"><label for="psgc-delete-reason">Reason</label><textarea id="psgc-delete-reason" name="reason" minlength="3" maxlength="500" required></textarea></div>
      <label class="checkbox-field"><input name="confirmed" type="checkbox" required /> I understand that this action cannot be undone.</label>
      <div class="dialog-actions"><button class="secondary-button" type="button" data-close>Cancel</button><button class="danger-button" type="submit"><span class="button-label">Delete permanently</span><span class="button-spinner"></span></button></div>
    </form>`);
  const form = dialogContent.querySelector("#psgc-delete-form");
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector('[type="submit"]');
    setButtonBusy(submit, true);
    setDialogError();
    try {
      await apiRequest(psgcDetailPath(detail), {
        method: "DELETE",
        body: { reason: form.elements.reason.value, confirmed: form.elements.confirmed.checked },
      });
      closeDialog();
      showToast("PSGC record permanently deleted.");
      await renderPsgcManagement();
    } catch (error) {
      setDialogError(psgcErrorMessage(error));
    } finally {
      setButtonBusy(submit, false);
    }
  });
}

function setupPsgcImport() {
  const importForm = document.querySelector("#psgc-import-form");
  const importFile = importForm.elements.file;
  const sourceVersion = importForm.elements.source_version;
  const previewButton = document.querySelector("#psgc-preview-button");
  const importButton = document.querySelector("#psgc-import-button");
  const importFeedback = document.querySelector("#psgc-import-feedback");
  const importPreview = document.querySelector("#psgc-import-preview");
  const importStatus = document.querySelector("#psgc-import-status");
  const importErrors = document.querySelector("#psgc-import-errors");
  let readyImport = null;

  const resetImportPreview = () => {
    readyImport = null;
    importPreview.hidden = true;
    importFeedback.hidden = true;
    importButton.hidden = true;
    importButton.disabled = true;
  };
  const showImportFeedback = (message) => {
    importFeedback.textContent = message;
    importFeedback.hidden = false;
  };
  const makeImportFormData = () => {
    const data = new FormData();
    data.append("source_version", sourceVersion.value.trim());
    data.append("file", importFile.files[0]);
    return data;
  };
  const showImportPreview = (preview, message) => {
    const counts = preview.counts || {};
    setText("#psgc-import-regions", formatNumber(counts.regions || 0));
    setText("#psgc-import-provinces", formatNumber(counts.provinces || 0));
    setText("#psgc-import-cities", formatNumber(counts.cities_municipalities || 0));
    setText("#psgc-import-barangays", formatNumber(counts.barangays || 0));
    importStatus.textContent = preview.valid ? `${message} Ready to import ${preview.file_name}.` : "No data was saved. Correct the listed file issues, then preview again.";
    importErrors.replaceChildren();
    for (const error of preview.errors || []) {
      const item = document.createElement("li");
      item.textContent = error;
      importErrors.append(item);
    }
    importErrors.hidden = !(preview.errors || []).length;
    importPreview.hidden = false;
    readyImport = preview.valid ? preview : null;
    importButton.hidden = !readyImport;
    importButton.disabled = !readyImport;
  };
  importFile.addEventListener("change", resetImportPreview);
  sourceVersion.addEventListener("input", resetImportPreview);
  importForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!importFile.files[0]) {
      showImportFeedback("Choose the official PSGC Excel file first.");
      return;
    }
    setButtonBusy(previewButton, true);
    importFeedback.hidden = true;
    try {
      const response = await apiRequest("/admin/psgc/imports/preview", { method: "POST", body: makeImportFormData() });
      showImportPreview(response.data, response.message);
    } catch (error) {
      showImportFeedback(error.message);
    } finally {
      setButtonBusy(previewButton, false);
    }
  });
  importButton.addEventListener("click", async () => {
    if (!readyImport || !importFile.files[0]) return;
    if (!window.confirm("Import this validated PSGC masterlist into the local lookup data?")) return;
    setButtonBusy(importButton, true);
    importFeedback.hidden = true;
    try {
      const response = await apiRequest("/admin/psgc/imports/apply", { method: "POST", body: makeImportFormData() });
      showToast(response.message);
      await renderPsgcManagement();
    } catch (error) {
      showImportFeedback(error.message);
    } finally {
      setButtonBusy(importButton, false);
    }
  });
}

async function renderPsgcManagement() {
  renderLoading();
  try {
    const [summaryResponse, workspaceData] = await Promise.all([
      apiRequest("/admin/psgc/summary"),
      loadPsgcWorkspace(),
    ]);
    const summary = summaryResponse.data;
    const isSearch = Boolean(state.psgc.search);
    const current = state.psgc.trail.at(-1);
    root.innerHTML = `
      <section class="view-intro"><div><h2>PSGC Reference Data</h2><p>Local Philippine Standard Geographic Code reference records.</p></div></section>
      <section class="summary-grid" aria-label="PSGC totals">
        <article class="summary-card"><span class="summary-label">Regions</span><strong class="summary-value">${formatNumber(summary.regions)}</strong></article>
        <article class="summary-card green"><span class="summary-label">Provinces</span><strong class="summary-value">${formatNumber(summary.provinces)}</strong></article>
        <article class="summary-card amber"><span class="summary-label">Cities / municipalities</span><strong class="summary-value">${formatNumber(summary.cities_municipalities)}</strong></article>
        <article class="summary-card"><span class="summary-label">Barangays</span><strong class="summary-value">${formatNumber(summary.barangays)}</strong></article>
      </section>
      <section class="panel psgc-workspace-panel">
        <header class="panel-header"><h3>${isSearch ? "PSGC search results" : "PSGC hierarchy"}</h3></header>
        <div class="panel-body psgc-workspace-body">
          <form id="psgc-search-form" class="toolbar psgc-toolbar">
            <div class="field-group search-field"><label for="psgc-search">Search</label><input id="psgc-search" name="search" type="search" value="${escapeHtml(state.psgc.search)}" placeholder="PSGC code or location name" /></div>
            <div class="field-group"><label for="psgc-level-filter">Level</label><select id="psgc-level-filter" name="level"><option value="">All levels</option><option value="region" ${state.psgc.level === "region" ? "selected" : ""}>Regions</option><option value="province" ${state.psgc.level === "province" ? "selected" : ""}>Provinces</option><option value="city_municipality" ${state.psgc.level === "city_municipality" ? "selected" : ""}>Cities / municipalities</option><option value="barangay" ${state.psgc.level === "barangay" ? "selected" : ""}>Barangays</option></select></div>
            <div class="field-group"><label for="psgc-status-filter">Status</label><select id="psgc-status-filter" name="status"><option value="active" ${state.psgc.status === "active" ? "selected" : ""}>Active</option><option value="inactive" ${state.psgc.status === "inactive" ? "selected" : ""}>Inactive</option><option value="all" ${state.psgc.status === "all" ? "selected" : ""}>All</option></select></div>
            <div class="psgc-toolbar-actions"><button class="primary-button" type="submit">Search</button><button id="psgc-clear-search" class="secondary-button" type="button">Clear</button></div>
          </form>
          <nav class="psgc-breadcrumb" aria-label="PSGC hierarchy">${psgcBreadcrumbMarkup()}</nav>
          <div class="psgc-current-level"><span>${isSearch ? "Search results" : `${current ? psgcLevelLabel(current.level) : "Regions"}`}</span><small>${isSearch ? "Open a result to inspect or browse its children." : "Select a location to move down the hierarchy."}</small></div>
          <div id="psgc-workspace-table" class="table-wrap"></div>
        </div>
      </section>
      <section class="panel psgc-import-panel">
        <header class="panel-header"><h3>Import PSA PSGC masterlist</h3></header>
        <form id="psgc-import-form" class="panel-body dialog-form">
          <div id="psgc-import-feedback" class="notice notice-error" role="alert" hidden></div>
          <div class="form-grid">
            <div class="field-group full-span"><label for="psgc-import-file">Official PSGC Excel file</label><input id="psgc-import-file" name="file" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required /></div>
            <div class="field-group"><label for="psgc-source-version">PSA release/version</label><input id="psgc-source-version" name="source_version" maxlength="120" placeholder="Example: PSGC 2Q 2026" required /></div>
          </div>
          <p class="field-help">Preview checks the Excel headers, PSGC codes, duplicates, and parent hierarchy before anything is saved.</p>
          <div class="dialog-actions"><button id="psgc-preview-button" class="secondary-button" type="submit"><span class="button-label">Preview file</span><span class="button-spinner"></span></button><button id="psgc-import-button" class="primary-button" type="button" hidden disabled><span class="button-label">Import masterlist</span><span class="button-spinner"></span></button></div>
          <section id="psgc-import-preview" class="psgc-import-preview" aria-live="polite" hidden>
            <p id="psgc-import-status" class="field-help"></p>
            <dl class="psgc-import-counts">
              <div><dt>Regions</dt><dd id="psgc-import-regions">0</dd></div>
              <div><dt>Provinces</dt><dd id="psgc-import-provinces">0</dd></div>
              <div><dt>Cities / municipalities</dt><dd id="psgc-import-cities">0</dd></div>
              <div><dt>Barangays</dt><dd id="psgc-import-barangays">0</dd></div>
            </dl>
            <ul id="psgc-import-errors" class="psgc-import-errors" hidden></ul>
          </section>
        </form>
      </section>`;
    renderPsgcWorkspaceTable(document.querySelector("#psgc-workspace-table"), workspaceData, isSearch);
    setupPsgcImport();
    document.querySelector("#psgc-search-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      state.psgc.search = form.elements.search.value.trim();
      state.psgc.level = form.elements.level.value;
      state.psgc.status = form.elements.status.value;
      state.psgc.page = 1;
      await renderPsgcManagement();
    });
    document.querySelector("#psgc-clear-search").addEventListener("click", async () => {
      state.psgc.search = "";
      state.psgc.level = "";
      state.psgc.page = 1;
      await renderPsgcManagement();
    });
    document.querySelector("#psgc-status-filter").addEventListener("change", async (event) => {
      state.psgc.status = event.currentTarget.value;
      state.psgc.page = 1;
      await renderPsgcManagement();
    });
    document.querySelectorAll("[data-psgc-trail-index]").forEach((button) => {
      button.addEventListener("click", async () => {
        const index = Number(button.dataset.psgcTrailIndex);
        state.psgc.trail = index < 0 ? [] : state.psgc.trail.slice(0, index + 1);
        state.psgc.search = "";
        state.psgc.page = 1;
        await renderPsgcManagement();
      });
    });
  } catch (error) {
    renderError(error, renderPsgcManagement);
  }
}

async function renderUsers() {
  renderLoading();
  try {
    const users = (await apiRequest("/users")).data;
    root.innerHTML = `
      <section class="view-intro"><div><h2>Admin Users</h2><p id="user-count"></p></div><button id="create-user" class="primary-button" type="button">Add admin user</button></section>
      <div class="toolbar"><div class="field-group search-field"><label for="user-search">Search</label><input id="user-search" type="search" placeholder="Name, email, role, or unit" /></div><div class="field-group"><label for="user-status">Status</label><select id="user-status"><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></div></div>
      <section class="panel"><div id="user-table" class="table-wrap"></div></section>`;
    setText("#user-count", `${formatNumber(users.length)} admin account${users.length === 1 ? "" : "s"}`);
    const draw = () => {
      const search = document.querySelector("#user-search").value.trim().toLowerCase();
      const status = document.querySelector("#user-status").value;
      const filtered = users.filter((user) => {
        const searchable = `${user.full_name} ${user.email} ${user.role.role_name} ${user.org_unit?.unit_name || ""}`.toLowerCase();
        return (!search || searchable.includes(search)) && (!status || user.account_status === status);
      });
      const container = document.querySelector("#user-table");
      if (!filtered.length) {
        renderEmpty(container, "No matching admin users", "Adjust the current filters.");
        return;
      }
      container.innerHTML = '<table class="data-table"><thead><tr><th>Admin user</th><th>Role</th><th>Organizational unit</th><th>Status</th><th>Action</th></tr></thead><tbody></tbody></table>';
      const tbody = container.querySelector("tbody");
      for (const user of filtered) {
        const row = document.createElement("tr");
        const identity = document.createElement("td");
        const name = document.createElement("div");
        name.className = "primary-cell";
        name.textContent = user.full_name;
        const email = document.createElement("div");
        email.className = "secondary-cell";
        email.textContent = user.email;
        identity.append(name, email);
        const statusCell = document.createElement("td");
        statusCell.append(badge(user.account_status));
        const actionCell = document.createElement("td");
        const action = document.createElement("button");
        action.type = "button";
        action.className = "table-button";
        action.textContent = "Manage";
        action.addEventListener("click", () => showUserDialog(user));
        actionCell.append(action);
        row.append(identity, cell(formatRole(user.role.role_name)), cell(user.org_unit?.unit_name), statusCell, actionCell);
        tbody.append(row);
      }
    };
    document.querySelector("#user-search").addEventListener("input", draw);
    document.querySelector("#user-status").addEventListener("change", draw);
    document.querySelector("#create-user").addEventListener("click", () => showUserDialog());
    draw();
  } catch (error) {
    renderError(error, renderUsers);
  }
}

async function showUserDialog(user = null) {
  openDialog(user ? "Manage admin user" : "Add admin user", `<form id="user-form" class="dialog-form"><p id="dialog-error" class="dialog-error" role="alert"></p><div class="form-grid"><div class="field-group full-span"><label for="admin-name">Full name</label><input id="admin-name" name="full_name" maxlength="150" required /></div><div class="field-group full-span"><label for="admin-email">Email address</label><input id="admin-email" name="email" type="email" maxlength="150" required /></div>${user ? "" : '<div class="field-group full-span"><label for="admin-password">Temporary password</label><input id="admin-password" name="password" type="password" minlength="8" maxlength="72" required /></div>'}<div class="field-group"><label for="admin-role">Role</label><select id="admin-role" name="role_id" required></select></div><div class="field-group"><label for="admin-unit">Organizational unit</label><select id="admin-unit" name="org_unit_id"></select></div></div><div class="dialog-actions">${user ? `<button id="user-status-action" class="${user.account_status === "active" ? "danger-button" : "secondary-button"}" type="button">${user.account_status === "active" ? "Deactivate account" : "Activate account"}</button>` : ""}<button class="secondary-button" type="button" data-close>Cancel</button><button class="primary-button" type="submit"><span class="button-label">Save user</span><span class="button-spinner"></span></button></div></form>`);
  const form = dialogContent.querySelector("#user-form");
  try {
    const [rolesResponse, unitsResponse] = await Promise.all([apiRequest("/roles"), apiRequest("/organizational-units")]);
    for (const role of rolesResponse.data) {
      const option = document.createElement("option");
      option.value = role.role_id;
      option.textContent = formatRole(role.role_name);
      form.elements.role_id.append(option);
    }
    const none = document.createElement("option");
    none.value = "";
    none.textContent = "No organizational unit";
    form.elements.org_unit_id.append(none);
    for (const unit of unitsResponse.data) {
      const option = document.createElement("option");
      option.value = unit.org_unit_id;
      option.textContent = unit.unit_name;
      form.elements.org_unit_id.append(option);
    }
    if (user) {
      form.elements.full_name.value = user.full_name;
      form.elements.email.value = user.email;
      form.elements.role_id.value = String(user.role.role_id);
      form.elements.org_unit_id.value = user.org_unit ? String(user.org_unit.org_unit_id) : "";
    }
  } catch (error) {
    setDialogError(error.message);
  }
  dialogContent.querySelector("[data-close]").addEventListener("click", closeDialog);
  dialogContent.querySelector("#user-status-action")?.addEventListener("click", async (clickEvent) => {
    const nextStatus = user.account_status === "active" ? "inactive" : "active";
    if (!window.confirm(`${nextStatus === "inactive" ? "Deactivate" : "Activate"} this account?`)) return;
    const button = clickEvent.currentTarget;
    setButtonBusy(button, true);
    try {
      await apiRequest(`/users/${user.user_id}/status`, { method: "PATCH", body: { account_status: nextStatus } });
      closeDialog();
      showToast("Admin account status updated.");
      renderUsers();
    } catch (error) {
      setDialogError(error.message);
    } finally {
      setButtonBusy(button, false);
    }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = form.querySelector('[type="submit"]');
    const payload = { full_name: form.elements.full_name.value, email: form.elements.email.value, role_id: Number(form.elements.role_id.value), org_unit_id: form.elements.org_unit_id.value ? Number(form.elements.org_unit_id.value) : null };
    if (!user) payload.password = form.elements.password.value;
    setButtonBusy(save, true);
    setDialogError();
    try {
      await apiRequest(user ? `/users/${user.user_id}` : "/users", { method: user ? "PATCH" : "POST", body: payload });
      closeDialog();
      showToast(user ? "Admin user updated." : "Admin user created.");
      renderUsers();
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
  menuButton.setAttribute("aria-expanded", "false");
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
    const active = item.dataset.view === requestedView;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
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
  const showSuperAdminNavigation = user.role.role_name === "super_admin";
  document.querySelector("#units-nav").hidden = !showSuperAdminNavigation;
  document.querySelector("#users-nav").hidden = !showSuperAdminNavigation;
  document.querySelector("#psgc-nav").hidden = !showSuperAdminNavigation;
  document.querySelector("#audit-nav").hidden = !showSuperAdminNavigation;
}

document.querySelector("#dialog-close").addEventListener("click", closeDialog);
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) closeDialog();
});
for (const item of document.querySelectorAll(".nav-item")) {
  item.addEventListener("click", () => navigate(item.dataset.view));
}
document.querySelector("#logout-button").addEventListener("click", logout);
menuButton.setAttribute("aria-controls", "sidebar");
menuButton.setAttribute("aria-expanded", "false");
menuButton.addEventListener("click", () => {
  sidebar.classList.add("open");
  scrim.hidden = false;
  menuButton.setAttribute("aria-expanded", "true");
});
scrim.addEventListener("click", closeSidebar);
refreshButton.addEventListener("click", async () => {
  setButtonBusy(refreshButton, true);
  try {
    await views[state.view].load();
    showToast("View refreshed.");
  } finally {
    setButtonBusy(refreshButton, false);
  }
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
