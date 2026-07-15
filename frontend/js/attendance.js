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
  root.innerHTML = `<section class="attendance-error"><div class="state-symbol" aria-hidden="true">!</div><strong></strong><span></span></section>`;
  root.querySelector("strong").textContent = title;
  root.querySelector("span").textContent = message;
}

function setFieldError(fieldName, message = "") {
  let normalizedName = fieldName;
  if (["region_code", "province_code", "city_municipality_code", "barangay_code"].includes(fieldName)) {
    normalizedName = "psgc_address";
  }
  if (["signature_text", "signature_image"].includes(fieldName)) {
    normalizedName = "signature";
  }
  const field = root.querySelector(`[data-field="${CSS.escape(normalizedName)}"]`);
  if (!field) return;
  const input = field.querySelector("input, select, textarea");
  if (input) input.setAttribute("aria-invalid", message ? "true" : "false");
  const error = field.querySelector(`[data-error-for="${CSS.escape(normalizedName)}"]`) || field.querySelector(":scope > .field-error");
  if (error) error.textContent = message;
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
}

function appendOptions(select, items, valueKey, labelBuilder) {
  for (const item of items) {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = labelBuilder(item);
    select.append(option);
  }
  select.disabled = false;
}

async function loadRegions() {
  const region = root.querySelector("#region-code");
  resetSelect(region, "Select region", true);
  const response = await apiRequest("/psgc/regions", { auth: false });
  appendOptions(region, response.data, "region_code", (item) => item.region_name);
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
    const response = await apiRequest(`/psgc/provinces?regionCode=${encodeURIComponent(region.value)}`, { auth: false });
    appendOptions(province, response.data, "province_code", (item) => item.province_name);
    await loadCities();
  } catch (error) {
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
    const response = await apiRequest(`/psgc/cities-municipalities?${query}`, { auth: false });
    appendOptions(city, response.data, "city_municipality_code", (item) => `${item.city_municipality_name} (${item.city_municipality_type})`);
  } catch (error) {
    setFieldError("psgc_address", error.message);
  }
}

async function loadBarangays() {
  const city = root.querySelector("#city-municipality-code");
  const barangay = root.querySelector("#barangay-code");
  resetSelect(barangay, "Select barangay");
  if (!city.value) return;
  try {
    const response = await apiRequest(`/psgc/barangays?cityMunicipalityCode=${encodeURIComponent(city.value)}`, { auth: false });
    appendOptions(barangay, response.data, "barangay_code", (item) => item.barangay_name);
  } catch (error) {
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
  root.querySelector("#consent-documentation-yes").required = requirements.consent_documentation_publication;
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
      <section class="form-section" data-field="signature" data-label-key="signature"><h2>${requiredLabel("signature", requirements)}</h2><div class="attendance-grid"><div class="field-group"><label for="signature-text">Typed full name</label><input id="signature-text" name="signature_text" maxlength="150" autocomplete="name" /><span class="field-error"></span></div><div class="field-group"><label for="signature-image">Signature image</label><input id="signature-image" name="signature_image" type="file" accept="image/png,image/jpeg" /><span class="field-error"></span></div></div><p class="field-help">Provide either a typed full name or a PNG/JPEG signature image when a signature is required.</p><span class="field-error" data-error-for="signature"></span></section>
      <section class="form-section"><h2>Consent</h2><div class="attendance-grid"><fieldset class="choice-field wide-field" data-field="consent_documentation_publication" data-label-key="consent_documentation_publication"><legend>${requiredLabel("consent_documentation_publication", requirements)}</legend><div class="choice-options"><label><input id="consent-documentation-yes" name="consent_documentation_publication" type="radio" value="true" /> Yes</label><label><input name="consent_documentation_publication" type="radio" value="false" /> No</label></div><span class="field-error"></span></fieldset><div class="wide-field" data-field="consent_database_processing" data-label-key="consent_database_processing"><label class="checkbox-field" for="consent-database-processing"><input id="consent-database-processing" name="consent_database_processing" type="checkbox" required /><span>${requiredLabel("consent_database_processing", requirements)}. I agree that my attendance information may be stored and processed for this event.</span></label><span class="field-error"></span></div></div></section>
      <div class="submit-row"><button id="attendance-submit" class="primary-button" type="submit"><span class="button-label">Submit attendance</span><span class="button-spinner"></span></button></div>
    </form>`;
  root.querySelector(".attendance-program").textContent = event.program.program_name;
  root.querySelector("h1").textContent = event.event_title;
  root.querySelector(".attendance-description").textContent = event.event_description || "";
  root.querySelector(".attendance-description").hidden = !event.event_description;
  root.querySelector("#event-date").textContent = formatDate(event.event_date);
  root.querySelector("#event-venue").textContent = event.venue;
  configureFieldSettings(requirements, visibility);
  attachAddressHandlers();
  loadRegions().catch((error) => setFieldError("psgc_address", error.message));
  root.querySelector("#attendance-form").addEventListener("submit", (submitEvent) => submitAttendance(submitEvent, event));
}

function validateBeforeSubmit(requirements, visibility) {
  let valid = true;
  const form = root.querySelector("#attendance-form");
  for (const input of form.querySelectorAll("input[required], select[required], textarea[required]")) {
    if (!input.checkValidity()) {
      const field = input.closest("[data-field]")?.dataset.field;
      if (field) setFieldError(field, "This field is required.");
      valid = false;
    }
  }
  if (visibility.signature && requirements.signature && !form.elements.signature_text.value.trim() && !form.elements.signature_image.files.length) {
    setFieldError("signature", "Provide a typed or uploaded signature.");
    valid = false;
  }
  const addressStarted = [form.elements.region_code.value, form.elements.province_code.value, form.elements.city_municipality_code.value, form.elements.barangay_code.value, form.elements.street_address.value.trim(), form.elements.postal_code.value.trim()].some(Boolean);
  if (visibility.psgc_address && (requirements.psgc_address || addressStarted) && (!form.elements.region_code.value || !form.elements.city_municipality_code.value || !form.elements.barangay_code.value)) {
    setFieldError("psgc_address", "Select region, city or municipality, and barangay.");
    valid = false;
  }
  return valid;
}

async function submitAttendance(event, publicEvent) {
  event.preventDefault();
  clearErrors();
  const requirements = publicEvent.attendance_field_requirements;
  const visibility = publicEvent.attendance_field_visibility;
  if (!validateBeforeSubmit(requirements, visibility)) return;
  const form = event.currentTarget;
  const submit = root.querySelector("#attendance-submit");
  submit.disabled = true;
  submit.classList.add("is-loading");
  const formData = new FormData(form);
  formData.set("consent_database_processing", String(form.elements.consent_database_processing.checked));
  formData.set("consent_documentation_publication", form.elements.consent_documentation_publication.value || "false");
  if (!form.elements.signature_image.files.length) formData.delete("signature_image");
  try {
    const response = await apiRequest(`/public/events/${encodeURIComponent(publicEvent.event_code)}/attendance`, { method: "POST", auth: false, body: formData });
    const data = response.data;
    root.innerHTML = '<section class="attendance-success"><div class="attendance-success-mark" aria-hidden="true">OK</div><strong>Attendance submitted</strong><span id="success-name"></span><span id="success-detail"></span></section>';
    root.querySelector("#success-name").textContent = data.attendee_name;
    root.querySelector("#success-detail").textContent = `Submitted on ${new Intl.DateTimeFormat("en-PH", { dateStyle: "medium", timeStyle: "short" }).format(new Date(data.submitted_at))}.`;
  } catch (error) {
    const feedback = root.querySelector("#attendance-feedback");
    feedback.textContent = error.message;
    feedback.hidden = false;
    for (const [field, message] of Object.entries(error.fields || {})) setFieldError(field, message);
  } finally {
    submit.disabled = false;
    submit.classList.remove("is-loading");
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
