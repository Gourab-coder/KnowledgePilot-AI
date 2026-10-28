const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

async function request(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(" ")
      : detail;
    throw new Error(message || `Request failed (${response.status}).`);
  }
  return data;
}

export const api = {
  register: (credentials) =>
    request("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    }),
  login: (credentials) =>
    request("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    }),
  me: (token) => request("/api/v1/auth/me", { token }),
  documents: (token) => request("/api/v1/documents", { token }),
  uploadDocument: (file, token) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/v1/documents", { method: "POST", token, body: form });
  },
  deleteDocument: (id, token) =>
    request(`/api/v1/documents/${id}`, { method: "DELETE", token }),
  conversations: (token) => request("/api/v1/conversations", { token }),
  messages: (id, token) => request(`/api/v1/conversations/${id}/messages`, { token }),
  chat: (payload, token) =>
    request("/api/v1/chat", {
      method: "POST",
      token,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
