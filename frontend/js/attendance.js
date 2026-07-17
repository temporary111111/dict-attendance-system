import { apiRequest } from "./api.js";

const root = document.querySelector("#attendance-root");
const eventCode = new URLSearchParams(window.location.search).get("event")?.trim();

const fieldLabels = {
  first_name: "First name",
  middle_name: "Middle name",
  last_name: "Last name",
  suffix: "Suffix",
  affiliation: "Affiliation or organization",
  designation_category: "Designation or category",
  sex: "Sex",
  email: "Email address",
  consent_documentation_publication: "Documentation and publication consent",
  consent_database_processing: "Database processing consent",
  signature: "Signature",
  psgc_address: "PSGC address",
  street_address: "Street address",
  postal_code: "Postal code",
};

let signaturePadState = null;

function formatDate(value) {
  return new Intl.DateTimeFormat("en-PH", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function requiredLabel(key, requirements) {
  return `${fieldLabels[key]}${requirements[key] ? ' <span class="required-mark" aria-label="required">*</span>' : ""}`;
}

function renderError(title, message) {
  root.innerHTML = `<section class="attendance-error" role="alert"><div class="state-symbol" aria-hidden="true">!</div><strong></strong><span></span></section>`;
  root.querySelector("strong").textContent = title;
  root.querySelector("span").textContent = message;
}

function setFieldError(fieldName, message = "") {
  let normalizedName = fieldName;
  if (["region_code", "province_code", "city_municipality_code", "barangay_code"].includes(fieldName)) {
    normalizedName = "psgc_address";
  }
  if (fieldName === "signature_image") {
    normalizedName = "signature";
  }
  const field = root.querySelector(`[data-field="${CSS.escape(normalizedName)}"]`);
  if (!field) return;
  const input = normalizedName === "signature"
    ? field.querySelector(".signature-method-button")
    : field.querySelector("input, select, textarea");
  if (input) input.setAttribute("aria-invalid", message ? "true" : "false");
  const error = field.querySelector(`[data-error-for="${CSS.escape(normalizedName)}"]`) || field.querySelector(":scope > .field-error");
  if (error) {
    error.id ||= `field-error-${normalizedName.replaceAll("_", "-")}`;
    error.setAttribute("aria-live", "polite");
    error.textContent = message;
    if (input) input.setAttribute("aria-describedby", error.id);
  }
  return input;
}

function clearErrors() {
  for (const field of root.querySelectorAll("[data-field]")) {
    const name = field.dataset.field;
    setFieldError(name);
  }
  const feedback = root.querySelector("#attendance-feedback");
  feedback.hidden = true;
  feedback.textContent = "";
}

function resetSelect(select, placeholder, disabled = true) {
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = placeholder;
  select.append(option);
  select.disabled = disabled;
  select.removeAttribute("aria-busy");
}

function setSelectLoading(select, message) {
  resetSelect(select, message, true);
  select.setAttribute("aria-busy", "true");
}

function appendOptions(select, items, valueKey, labelBuilder) {
  for (const item of items) {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = labelBuilder(item);
    select.append(option);
  }
  select.disabled = items.length === 0;
  select.removeAttribute("aria-busy");
}

async function loadRegions() {
  const region = root.querySelector("#region-code");
  setSelectLoading(region, "Loading regions...");
  try {
    const response = await apiRequest("/psgc/regions", { auth: false });
    appendOptions(region, response.data, "region_code", (item) => item.region_name);
  } catch (error) {
    resetSelect(region, "Unable to load regions");
    throw error;
  }
}

async function loadProvincesAndCities() {
  const region = root.querySelector("#region-code");
  const province = root.querySelector("#province-code");
  const city = root.querySelector("#city-municipality-code");
  const barangay = root.querySelector("#barangay-code");
  resetSelect(province, "Select province (if applicable)");
  resetSelect(city, "Select city or municipality");
  resetSelect(barangay, "Select barangay");
  if (!region.value) return;
  try {
    setSelectLoading(province, "Loading provinces...");
    const response = await apiRequest(`/psgc/provinces?regionCode=${encodeURIComponent(region.value)}`, { auth: false });
    appendOptions(province, response.data, "province_code", (item) => item.province_name);
    await loadCities();
  } catch (error) {
    resetSelect(province, "Unable to load provinces");
    setFieldError("psgc_address", error.message);
  }
}

async function loadCities() {
  const region = root.querySelector("#region-code");
  const province = root.querySelector("#province-code");
  const city = root.querySelector("#city-municipality-code");
  const barangay = root.querySelector("#barangay-code");
  resetSelect(city, "Select city or municipality");
  resetSelect(barangay, "Select barangay");
  if (!region.value) return;
  const query = new URLSearchParams({ regionCode: region.value });
  if (province.value) query.set("provinceCode", province.value);
  try {
    setSelectLoading(city, "Loading cities or municipalities...");
    const response = await apiRequest(`/psgc/cities-municipalities?${query}`, { auth: false });
    appendOptions(city, response.data, "city_municipality_code", (item) => `${item.city_municipality_name} (${item.city_municipality_type})`);
  } catch (error) {
    resetSelect(city, "Unable to load cities or municipalities");
    setFieldError("psgc_address", error.message);
  }
}

async function loadBarangays() {
  const city = root.querySelector("#city-municipality-code");
  const barangay = root.querySelector("#barangay-code");
  resetSelect(barangay, "Select barangay");
  if (!city.value) return;
  try {
    setSelectLoading(barangay, "Loading barangays...");
    const response = await apiRequest(`/psgc/barangays?cityMunicipalityCode=${encodeURIComponent(city.value)}`, { auth: false });
    appendOptions(barangay, response.data, "barangay_code", (item) => item.barangay_name);
  } catch (error) {
    resetSelect(barangay, "Unable to load barangays");
    setFieldError("psgc_address", error.message);
  }
}

function attachAddressHandlers() {
  root.querySelector("#region-code").addEventListener("change", loadProvincesAndCities);
  root.querySelector("#province-code").addEventListener("change", loadCities);
  root.querySelector("#city-municipality-code").addEventListener("change", loadBarangays);
}

function configureFieldSettings(requirements, visibility) {
  for (const [key, required] of Object.entries(requirements)) {
    const field = root.querySelector(`[data-field="${CSS.escape(key)}"]`);
    if (!field) continue;
    const input = field.querySelector("input, select, textarea");
    if (input && input.type !== "checkbox" && key !== "signature") input.required = required;
  }
  root.querySelector("#consent-database-processing").required = true;
  root.querySelector("#consent-documentation-publication").required = requirements.consent_documentation_publication;
  for (const [key, isVisible] of Object.entries(visibility)) {
    const field = root.querySelector(`[data-field="${CSS.escape(key)}"]`);
    if (!field || isVisible) continue;
    field.hidden = true;
    for (const control of field.querySelectorAll("input, select, textarea")) {
      control.disabled = true;
      control.required = false;
    }
  }
}

function hasDrawnSignature() {
  return Boolean(
    signaturePadState?.mode === "draw" && signaturePadState.hasInk
  );
}

function clearDrawnSignature() {
  if (!signaturePadState) return;
  const { canvas, context } = signaturePadState;
  context.clearRect(0, 0, canvas.width, canvas.height);
  signaturePadState.hasInk = false;
  setFieldError("signature");
}

function initializeSignaturePad() {
  const canvas = root.querySelector("#signature-pad");
  const clearButton = root.querySelector("#clear-drawn-signature");
  const context = canvas.getContext("2d");
  context.lineCap = "round";
  context.lineJoin = "round";
  context.lineWidth = 5;
  context.strokeStyle = "#17202a";
  context.fillStyle = "#17202a";

  signaturePadState = {
    canvas,
    context,
    hasInk: false,
    activePointerId: null,
    lastPoint: null,
    mode: "draw",
  };
  const drawModeButton = root.querySelector("#signature-mode-draw");
  const uploadModeButton = root.querySelector("#signature-mode-upload");
  const drawPanel = root.querySelector("#signature-draw-panel");
  const uploadPanel = root.querySelector("#signature-upload-panel");
  const uploadInput = root.querySelector("#signature-image");

  const setSignatureMode = (mode) => {
    signaturePadState.mode = mode;
    const isDrawMode = mode === "draw";
    drawPanel.hidden = !isDrawMode;
    uploadPanel.hidden = isDrawMode;
    uploadInput.disabled = isDrawMode;
    drawModeButton.setAttribute("aria-pressed", String(isDrawMode));
    uploadModeButton.setAttribute("aria-pressed", String(!isDrawMode));
  };

  const pointFromEvent = (pointerEvent) => {
    const bounds = canvas.getBoundingClientRect();
    return {
      x: (pointerEvent.clientX - bounds.left) * (canvas.width / bounds.width),
      y: (pointerEvent.clientY - bounds.top) * (canvas.height / bounds.height),
    };
  };
  const stopDrawing = (pointerEvent) => {
    if (signaturePadState.activePointerId !== pointerEvent.pointerId) return;
    signaturePadState.activePointerId = null;
    signaturePadState.lastPoint = null;
    if (canvas.hasPointerCapture?.(pointerEvent.pointerId)) {
      canvas.releasePointerCapture(pointerEvent.pointerId);
    }
  };

  canvas.addEventListener("pointerdown", (pointerEvent) => {
    if (pointerEvent.pointerType === "mouse" && pointerEvent.button !== 0) return;
    pointerEvent.preventDefault();
    const point = pointFromEvent(pointerEvent);
    signaturePadState.activePointerId = pointerEvent.pointerId;
    signaturePadState.lastPoint = point;
    signaturePadState.hasInk = true;
    canvas.setPointerCapture?.(pointerEvent.pointerId);
    context.beginPath();
    context.arc(point.x, point.y, context.lineWidth / 2, 0, Math.PI * 2);
    context.fill();
  });
  canvas.addEventListener("pointermove", (pointerEvent) => {
    if (signaturePadState.activePointerId !== pointerEvent.pointerId) return;
    pointerEvent.preventDefault();
    const point = pointFromEvent(pointerEvent);
    context.beginPath();
    context.moveTo(signaturePadState.lastPoint.x, signaturePadState.lastPoint.y);
    context.lineTo(point.x, point.y);
    context.stroke();
    signaturePadState.lastPoint = point;
  });
  canvas.addEventListener("pointerup", stopDrawing);
  canvas.addEventListener("pointercancel", stopDrawing);
  clearButton.addEventListener("click", clearDrawnSignature);
  drawModeButton.addEventListener("click", () => setSignatureMode("draw"));
  uploadModeButton.addEventListener("click", () => setSignatureMode("upload"));
  setSignatureMode("draw");
}

function drawnSignatureBlob() {
  if (!hasDrawnSignature()) return Promise.resolve(null);
  return new Promise((resolve) => {
    signaturePadState.canvas.toBlob(resolve, "image/png");
  });
}

function confirmConsentBeforeSubmitting(publicEvent) {
  const dialog = root.querySelector("#consent-confirmation-dialog");
  const publicationSummary = dialog.querySelector("#publication-consent-summary");
  const publicationConsent = root.querySelector("#consent-documentation-publication");
  const backButton = dialog.querySelector("#consent-review-button");
  const confirmButton = dialog.querySelector("#consent-confirm-button");
  const publicationVisible = publicEvent.attendance_field_visibility.consent_documentation_publication;

  if (!publicationVisible) {
    publicationSummary.textContent = "This event does not request documentation or publication consent.";
  } else if (publicationConsent.checked) {
    publicationSummary.textContent = "You consented to having your photos, videos, and audio recorded during the event and included in DICT publications, if needed.";
  } else {
    publicationSummary.textContent = "You are submitting without documentation or publication consent for this event.";
  }

  return new Promise((resolve) => {
    const finish = () => {
      const confirmed = dialog.returnValue === "confirm";
      backButton.removeEventListener("click", review);
      confirmButton.removeEventListener("click", confirm);
      dialog.removeEventListener("close", finish);
      resolve(confirmed);
    };
    const review = () => dialog.close("review");
    const confirm = () => dialog.close("confirm");
    backButton.addEventListener("click", review);
    confirmButton.addEventListener("click", confirm);
    dialog.addEventListener("close", finish);
    dialog.showModal();
  });
}

function renderAttendanceForm(event) {
  const requirements = event.attendance_field_requirements;
  const visibility = event.attendance_field_visibility;
  root.innerHTML = `
    <section class="attendance-event">
      <p class="attendance-program"></p>
      <h1></h1>
      <p class="attendance-description"></p>
      <div class="event-details"><span id="event-date"></span><span id="event-venue"></span></div>
    </section>
    <section class="privacy-notice" aria-labelledby="privacy-notice-title">
      <h2 id="privacy-notice-title">Privacy Notice</h2>
      <p>The DICT collects your personal data through this digital attendance form to provide verifiable evidence and documentation of your participation in this event, as well as for monitoring and evaluation purposes.</p>
      <p>Your information will be stored in the DICT database or other secured repositories for three (3) years before being permanently erased from our records.</p>
      <p>Photos, videos, and audio recordings may be taken throughout the event for documentation and may be used in official DICT publications, if needed. Should you wish to withdraw your consent, please contact the respective event organizers.</p>
    </section>
    <form id="attendance-form" class="attendance-form" novalidate enctype="multipart/form-data">
      <div id="attendance-feedback" class="notice notice-error form-feedback" role="alert" hidden></div>
      <section class="form-section"><h2>Attendee information</h2><div class="attendance-grid">
        <div class="field-group" data-field="first_name" data-label-key="first_name"><label for="first-name">${requiredLabel("first_name", requirements)}</label><input id="first-name" name="first_name" maxlength="100" autocomplete="given-name" required /><span class="field-error"></span></div>
        <div class="field-group" data-field="middle_name" data-label-key="middle_name"><label for="middle-name">${requiredLabel("middle_name", requirements)}</label><input id="middle-name" name="middle_name" maxlength="100" autocomplete="additional-name" /><span class="field-error"></span></div>
        <div class="field-group" data-field="last_name" data-label-key="last_name"><label for="last-name">${requiredLabel("last_name", requirements)}</label><input id="last-name" name="last_name" maxlength="100" autocomplete="family-name" required /><span class="field-error"></span></div>
        <div class="field-group" data-field="suffix" data-label-key="suffix"><label for="suffix">${requiredLabel("suffix", requirements)}</label><input id="suffix" name="suffix" maxlength="30" autocomplete="honorific-suffix" /><span class="field-error"></span></div>
        <div class="field-group wide-field" data-field="email" data-label-key="email"><label for="email">${requiredLabel("email", requirements)}</label><input id="email" name="email" type="email" maxlength="150" inputmode="email" autocomplete="email" required /><span class="field-error"></span></div>
        <div class="field-group wide-field" data-field="affiliation" data-label-key="affiliation"><label for="affiliation">${requiredLabel("affiliation", requirements)}</label><input id="affiliation" name="affiliation" maxlength="200" /><span class="field-error"></span></div>
        <div class="field-group" data-field="designation_category" data-label-key="designation_category"><label for="designation-category">${requiredLabel("designation_category", requirements)}</label><input id="designation-category" name="designation_category" maxlength="150" /><span class="field-error"></span></div>
        <div class="field-group" data-field="sex" data-label-key="sex"><label for="sex">${requiredLabel("sex", requirements)}</label><select id="sex" name="sex"><option value="">Select</option><option value="F">Female</option><option value="M">Male</option></select><span class="field-error"></span></div>
      </div></section>
      <section class="form-section" data-field="psgc_address" data-label-key="psgc_address"><h2>${requiredLabel("psgc_address", requirements)}</h2><p class="address-note">Select your Philippine Standard Geographic Code address when applicable.</p><div class="attendance-grid">
        <div class="field-group"><label for="region-code">Region</label><select id="region-code" name="region_code"></select></div>
        <div class="field-group"><label for="province-code">Province</label><select id="province-code" name="province_code"></select></div>
        <div class="field-group"><label for="city-municipality-code">City or municipality</label><select id="city-municipality-code" name="city_municipality_code"></select></div>
        <div class="field-group"><label for="barangay-code">Barangay</label><select id="barangay-code" name="barangay_code"></select></div>
        <div class="field-group" data-field="street_address" data-label-key="street_address"><label for="street-address">${requiredLabel("street_address", requirements)}</label><input id="street-address" name="street_address" maxlength="255" autocomplete="street-address" /><span class="field-error"></span></div>
        <div class="field-group" data-field="postal_code" data-label-key="postal_code"><label for="postal-code">${requiredLabel("postal_code", requirements)}</label><input id="postal-code" name="postal_code" maxlength="10" inputmode="numeric" autocomplete="postal-code" /><span class="field-error"></span></div>
      </div><span class="field-error" data-error-for="psgc_address"></span></section>
      <section class="form-section" data-field="signature" data-label-key="signature"><h2>${requiredLabel("signature", requirements)}</h2><div class="signature-methods" role="group" aria-label="Signature method"><button id="signature-mode-draw" class="signature-method-button" type="button" aria-pressed="true">Draw signature</button><button id="signature-mode-upload" class="signature-method-button" type="button" aria-pressed="false">Upload image</button></div><div id="signature-draw-panel" class="field-group"><label for="signature-pad">Draw your signature</label><canvas id="signature-pad" class="signature-pad" width="900" height="250" aria-label="Draw your signature using a mouse, finger, or stylus">Your browser does not support digital signature drawing.</canvas><div class="signature-pad-actions"><button id="clear-drawn-signature" class="secondary-button" type="button">Clear drawing</button></div></div><div id="signature-upload-panel" class="field-group" hidden><label for="signature-image">Upload a PNG or JPEG signature image</label><input id="signature-image" name="signature_image" type="file" accept="image/png,image/jpeg" disabled /><span class="field-error"></span></div><p class="field-help">Choose one signature method. Provide a signature when this field is required.</p><span class="field-error" data-error-for="signature"></span></section>
      <section class="form-section"><h2>Consent</h2><div class="attendance-grid"><div class="wide-field" data-field="consent_documentation_publication" data-label-key="consent_documentation_publication"><label class="checkbox-field" for="consent-documentation-publication"><input id="consent-documentation-publication" name="consent_documentation_publication" type="checkbox" /><span>${requiredLabel("consent_documentation_publication", requirements)}. I consent to having my photos, videos, and audio recorded during the event and included in DICT publications, if needed.</span></label><span class="field-error"></span></div><div class="wide-field" data-field="consent_database_processing" data-label-key="consent_database_processing"><label class="checkbox-field" for="consent-database-processing"><input id="consent-database-processing" name="consent_database_processing" type="checkbox" required /><span>${requiredLabel("consent_database_processing", requirements)}. I consent to the inclusion of my personal information in the organizer's database for future processing of relevant documents.</span></label><span class="field-error"></span></div></div></section>
      <div class="submit-row"><button id="attendance-submit" class="primary-button" type="submit"><span class="button-label">Submit attendance</span><span class="button-spinner"></span></button></div>
    </form>
    <dialog id="consent-confirmation-dialog" class="consent-confirmation-dialog" aria-labelledby="consent-confirmation-title">
      <section class="consent-confirmation-content">
        <h2 id="consent-confirmation-title">Review your consent</h2>
        <p>Please review the Privacy Notice and confirm your consent before submitting your attendance.</p>
        <ul class="consent-summary-list">
          <li>You consented to the inclusion of your personal information in the organizer's database for future processing of relevant documents.</li>
          <li id="publication-consent-summary"></li>
        </ul>
        <div class="consent-confirmation-actions">
          <button id="consent-review-button" class="secondary-button" type="button" autofocus>Back and review</button>
          <button id="consent-confirm-button" class="primary-button" type="button">Confirm and submit</button>
        </div>
      </section>
    </dialog>`;
  root.querySelector(".attendance-program").textContent = event.program.program_name;
  root.querySelector("h1").textContent = event.event_title;
  root.querySelector(".attendance-description").textContent = event.event_description || "";
  root.querySelector(".attendance-description").hidden = !event.event_description;
  root.querySelector("#event-date").textContent = formatDate(event.event_date);
  root.querySelector("#event-venue").textContent = event.venue;
  configureFieldSettings(requirements, visibility);
  initializeSignaturePad();
  attachAddressHandlers();
  loadRegions().catch((error) => setFieldError("psgc_address", error.message));
  root.querySelector("#attendance-form").addEventListener("submit", (submitEvent) => submitAttendance(submitEvent, event));
}

function focusFirstInvalidField() {
  const field = root.querySelector('[aria-invalid="true"]');
  if (!field) return;
  field.focus({ preventScroll: true });
  field.scrollIntoView({ behavior: "smooth", block: "center" });
}

function requiredFieldMessage(input) {
  if (input.type === "checkbox") return "This consent is required before you can submit attendance.";
  if (input.type === "email" && input.validity.typeMismatch) return "Enter a valid email address.";
  return "This field is required.";
}

function validateBeforeSubmit(requirements, visibility) {
  let valid = true;
  const form = root.querySelector("#attendance-form");
  for (const input of form.querySelectorAll("input[required], select[required], textarea[required]")) {
    if (!input.checkValidity()) {
      const field = input.closest("[data-field]")?.dataset.field;
      if (field) setFieldError(field, requiredFieldMessage(input));
      valid = false;
    }
  }
  const uploadedSignatureSelected = signaturePadState?.mode === "upload" && form.elements.signature_image.files.length;
  if (visibility.signature && requirements.signature && !hasDrawnSignature() && !uploadedSignatureSelected) {
    setFieldError("signature", "Draw your signature or upload a signature image.");
    valid = false;
  }
  const addressStarted = [form.elements.region_code.value, form.elements.province_code.value, form.elements.city_municipality_code.value, form.elements.barangay_code.value, form.elements.street_address.value.trim(), form.elements.postal_code.value.trim()].some(Boolean);
  if (visibility.psgc_address && (requirements.psgc_address || addressStarted) && (!form.elements.region_code.value || !form.elements.city_municipality_code.value || !form.elements.barangay_code.value)) {
    setFieldError("psgc_address", "Select region, city or municipality, and barangay.");
    valid = false;
  }
  if (!valid) focusFirstInvalidField();
  return valid;
}

async function submitAttendance(event, publicEvent) {
  event.preventDefault();
  const form = event.currentTarget;
  clearErrors();
  const requirements = publicEvent.attendance_field_requirements;
  const visibility = publicEvent.attendance_field_visibility;
  if (!validateBeforeSubmit(requirements, visibility)) return;
  const drawnSignature = visibility.signature ? await drawnSignatureBlob() : null;
  if (hasDrawnSignature() && drawnSignature === null) {
    setFieldError("signature", "Unable to prepare your drawn signature. Please draw it again.");
    return;
  }
  if (!(await confirmConsentBeforeSubmitting(publicEvent))) return;
  const submit = root.querySelector("#attendance-submit");
  submit.disabled = true;
  submit.classList.add("is-loading");
  submit.setAttribute("aria-busy", "true");
  const formData = new FormData(form);
  formData.set("consent_database_processing", String(form.elements.consent_database_processing.checked));
  formData.set("consent_documentation_publication", String(form.elements.consent_documentation_publication.checked));
  formData.delete("signature_image");
  if (drawnSignature !== null) {
    formData.set("signature_image", drawnSignature, "drawn-signature.png");
  } else if (signaturePadState?.mode === "upload" && form.elements.signature_image.files.length) {
    formData.set("signature_image", form.elements.signature_image.files[0]);
  }
  try {
    const response = await apiRequest(`/public/events/${encodeURIComponent(publicEvent.event_code)}/attendance`, { method: "POST", auth: false, body: formData });
    const data = response.data;
    root.innerHTML = '<section class="attendance-success" role="status"><div class="attendance-success-mark" aria-hidden="true">OK</div><strong>Attendance submitted</strong><span id="success-name"></span><span id="success-detail"></span></section>';
    root.querySelector("#success-name").textContent = data.attendee_name;
    root.querySelector("#success-detail").textContent = `Submitted on ${new Intl.DateTimeFormat("en-PH", { dateStyle: "medium", timeStyle: "short" }).format(new Date(data.submitted_at))}.`;
  } catch (error) {
    const feedback = root.querySelector("#attendance-feedback");
    feedback.textContent = error.message;
    feedback.hidden = false;
    feedback.tabIndex = -1;
    for (const [field, message] of Object.entries(error.fields || {})) setFieldError(field, message);
    feedback.focus({ preventScroll: true });
    feedback.scrollIntoView({ behavior: "smooth", block: "center" });
  } finally {
    submit.disabled = false;
    submit.classList.remove("is-loading");
    submit.setAttribute("aria-busy", "false");
  }
}

async function initialize() {
  if (!eventCode) {
    renderError("Event link is incomplete", "Use the attendance link or QR code provided by the event administrator.");
    return;
  }
  try {
    const event = (await apiRequest(`/public/events/${encodeURIComponent(eventCode)}`, { auth: false })).data;
    document.title = `${event.event_title} | DICT Attendance`;
    if (!event.accepting_attendance) {
      renderError("Attendance is not open", "This event is currently not accepting attendance submissions.");
      return;
    }
    renderAttendanceForm(event);
  } catch (error) {
    renderError("Attendance form unavailable", error.message);
  }
}

await initialize();
