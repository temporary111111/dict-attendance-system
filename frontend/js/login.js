import { apiRequest, getApiOrigin, saveSession } from "./api.js";
import { requireGuest } from "./auth.js";

const form = document.querySelector("#login-form");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const rememberInput = document.querySelector("#remember");
const submitButton = document.querySelector("#login-button");
const passwordToggle = document.querySelector("#toggle-password");
const errorBox = document.querySelector("#login-error");
const sessionMessage = document.querySelector("#session-message");
const connectionDot = document.querySelector("#connection-dot");
const connectionText = document.querySelector("#connection-text");

function setFieldError(input, message) {
  input.setAttribute("aria-invalid", message ? "true" : "false");
  document.querySelector(`#${input.id}-error`).textContent = message;
}

function validate() {
  let valid = true;
  let firstInvalid = null;
  setFieldError(emailInput, "");
  setFieldError(passwordInput, "");

  if (!emailInput.validity.valid) {
    setFieldError(emailInput, "Enter a valid admin email address.");
    valid = false;
    firstInvalid = emailInput;
  }
  if (!passwordInput.value) {
    setFieldError(passwordInput, "Enter your password.");
    valid = false;
    firstInvalid ||= passwordInput;
  }
  firstInvalid?.focus();
  return valid;
}

function setSubmitting(isSubmitting) {
  submitButton.disabled = isSubmitting;
  submitButton.classList.toggle("is-loading", isSubmitting);
  emailInput.disabled = isSubmitting;
  passwordInput.disabled = isSubmitting;
  rememberInput.disabled = isSubmitting;
  passwordToggle.disabled = isSubmitting;
}

async function checkBackend() {
  try {
    await apiRequest("/health", { auth: false });
    connectionDot.className = "connection-dot online";
    connectionText.textContent = `Connected to ${getApiOrigin()}`;
  } catch {
    connectionDot.className = "connection-dot offline";
    connectionText.textContent = `Backend unavailable at ${getApiOrigin()}`;
  }
}

passwordToggle.addEventListener("click", (event) => {
  const showing = passwordInput.type === "text";
  passwordInput.type = showing ? "password" : "text";
  event.currentTarget.textContent = showing ? "Show" : "Hide";
  event.currentTarget.setAttribute("aria-pressed", String(!showing));
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  if (!validate()) return;

  setSubmitting(true);
  try {
    const response = await apiRequest("/auth/login", {
      method: "POST",
      auth: false,
      body: {
        email: emailInput.value.trim(),
        password: passwordInput.value,
      },
    });
    saveSession(
      response.data.access_token,
      response.data.expires_in_minutes,
      rememberInput.checked,
    );
    window.location.replace("./admin.html");
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
    passwordInput.focus();
    passwordInput.select();
  } finally {
    setSubmitting(false);
  }
});

const params = new URLSearchParams(window.location.search);
if (params.has("expired")) {
  sessionMessage.textContent = "Your session expired. Sign in again.";
  sessionMessage.hidden = false;
}

await requireGuest();
await checkBackend();
