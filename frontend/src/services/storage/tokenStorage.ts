const ACCESS_TOKEN_KEY = "biztracker.access_token";
const AUTH_CHANGED_EVENT = "biztracker-auth-changed";

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  emitAuthChanged();
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  emitAuthChanged();
}

export function subscribeToAuthChanges(callback: () => void): () => void {
  window.addEventListener(AUTH_CHANGED_EVENT, callback);
  window.addEventListener("storage", callback);

  return () => {
    window.removeEventListener(AUTH_CHANGED_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function emitAuthChanged(): void {
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
}
