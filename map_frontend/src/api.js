function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(^| )" + name + "=([^;]+)")
  );
  return match ? decodeURIComponent(match[2]) : null;
}

async function request(url, options = {}) {
  const headers = options.headers || {};

  if (options.method && options.method !== "GET") {
    headers["X-CSRFToken"] = getCookie("csrftoken");
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

// Django's CSRF cookie is only set once a view that calls
// django.middleware.csrf.get_token runs; GET /api/spots/ (behind
// SessionAuthentication + CsrfViewMiddleware) does this for us on load.
export function getSpots() {
  return request("/map/api/spots/");
}

export function createSpot(name, lat, lng) {
  const body = new URLSearchParams({ name, lat, lng });
  return request("/map/api/spots/", { method: "POST", body });
}

export function deleteSpot(spotId) {
  return request(`/map/api/spots/${spotId}/`, { method: "DELETE" });
}

export function uploadPhoto(spotId, file) {
  const body = new FormData();
  body.append("image", file);
  return request(`/map/api/spots/${spotId}/photos/`, { method: "POST", body });
}

export function approvePhoto(spotId, photoId) {
  return request(`/map/api/spots/${spotId}/photos/${photoId}/approve/`, {
    method: "POST",
  });
}

export function rejectPhoto(spotId, photoId) {
  return request(`/map/api/spots/${spotId}/photos/${photoId}/`, {
    method: "DELETE",
  });
}

export function changeMainImage(spotId, file) {
  const body = new FormData();
  body.append("image", file);
  return request(`/map/api/spots/${spotId}/main-image/`, {
    method: "POST",
    body,
  });
}

export function adminLogin(username, password) {
  const body = new URLSearchParams({ username, password });
  return request("/map/api/admin/login/", { method: "POST", body });
}

export function adminLogout() {
  return request("/map/api/admin/logout/", { method: "POST" });
}

export function adminStatus() {
  return request("/map/api/admin/status/");
}
