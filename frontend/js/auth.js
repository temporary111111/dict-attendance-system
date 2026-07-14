import { apiRequest, clearSession, getAccessToken } from "./api.js";

export function redirectToAdmin() {
  window.location.replace("./admin.html");
}

export function redirectToLogin() {
  window.location.replace("./index.html");
}

export async function requireGuest() {
  if (!getAccessToken()) return;
  try {
    await apiRequest("/auth/me");
    redirectToAdmin();
  } catch {
    clearSession();
  }
}

export async function requireAdmin() {
  if (!getAccessToken()) {
    redirectToLogin();
    return null;
  }
  try {
    const response = await apiRequest("/auth/me");
    return response.data;
  } catch {
    clearSession();
    redirectToLogin();
    return null;
  }
}

export async function logout() {
  try {
    await apiRequest("/auth/logout", { method: "POST" });
  } catch {
    // Stateless ang logout; local token removal pa rin ang final action.
  }
  clearSession();
  redirectToLogin();
}
