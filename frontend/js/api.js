const API_BASE_URL = String(
  window.APP_CONFIG?.apiBaseUrl || "http://127.0.0.1:8000/api",
).replace(/\/$/, "");

const TOKEN_KEY = "dict_attendance_access_token";
const EXPIRY_KEY = "dict_attendance_token_expires_at";

export class ApiError extends Error {
  constructor(message, { status = 0, code = "REQUEST_FAILED", fields = {} } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

function activeStorage() {
  if (localStorage.getItem(TOKEN_KEY)) return localStorage;
  return sessionStorage;
}

export function getAccessToken() {
  const storage = activeStorage();
  const token = storage.getItem(TOKEN_KEY);
  const expiry = Number(storage.getItem(EXPIRY_KEY) || 0);

  if (token && expiry && Date.now() >= expiry) {
    clearSession();
    return null;
  }
  return token;
}

export function saveSession(accessToken, expiresInMinutes, remember) {
  clearSession();
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem(TOKEN_KEY, accessToken);
  storage.setItem(
    EXPIRY_KEY,
    String(Date.now() + Number(expiresInMinutes) * 60_000),
  );
}

export function clearSession() {
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(TOKEN_KEY);
    storage.removeItem(EXPIRY_KEY);
  }
}

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export function getApiOrigin() {
  return new URL(API_BASE_URL).origin;
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getAccessToken();
  const isFormData = options.body instanceof FormData;

  if (options.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;
  try {
    response = await fetch(apiUrl(path), {
      ...options,
      headers,
      body:
        options.body && !isFormData && typeof options.body !== "string"
          ? JSON.stringify(options.body)
          : options.body,
    });
  } catch {
    throw new ApiError("Hindi ma-connect sa backend server.", {
      code: "NETWORK_ERROR",
    });
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const error = payload?.error || payload?.detail?.error || {};
    if (response.status === 401 && options.auth !== false) {
      clearSession();
      window.location.replace("./index.html?expired=1");
    }
    throw new ApiError(error.message || `Request failed (${response.status}).`, {
      status: response.status,
      code: error.code,
      fields: error.fields,
    });
  }

  return payload;
}
