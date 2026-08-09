const trek_manager = (() => {
  const TOKEN_KEY = "tma_token";
  const USER_KEY = "tma_user";

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }
  function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  async function request(method, endPoint, body) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`/api${endPoint}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    let data = {};
    try { data = await response.json(); } catch (e) { /* no body */ }

    if (response.status === 401) {
      clearSession();
      window.location.hash = "#/login";
    }
    if (!response.ok) {
      const err = new Error(data.error || `Request failed (${response.status})`);
      err.fields = data.fields || null;
      err.status = response.status;
      throw err;
    }
    return data;
  }
  async function downloadFile(endPoint, filename) {
    const token = getToken();
    const response = await fetch(`/api${endPoint}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) throw new Error("Download failed.");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    window.URL.revokeObjectURL(url);
  }

  return {
    get: (endPoint) => request("GET", endPoint),
    post: (endPoint, body) => request("POST", endPoint, body),
    put: (endPoint, body) => request("PUT", endPoint, body),
    del: (endPoint) => request("DELETE", endPoint),
    getToken, getUser, setSession, clearSession, downloadFile,
  };
})();
