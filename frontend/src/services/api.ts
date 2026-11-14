import type { AuthResponse, SearchHistoryEntry, SearchResponse, Track, User } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
const TOKEN_KEY = "moodify.access-token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new Error("Не удалось связаться с сервером. Запустите Moodify и повторите попытку.");
  }
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join("; ") : detail || "Запрос не выполнен.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  search: (query: string, genre: string | null) =>
    request<SearchResponse>("/search", { method: "POST", body: JSON.stringify({ query, genre, limit: 12 }) }),
  tracks: (genre?: string) => request<Track[]>(`/tracks${genre ? `?genre=${encodeURIComponent(genre)}` : ""}`),
  favorites: () => request<Track[]>("/favorites"),
  addFavorite: (trackId: string) => request<{ message: string }>(`/favorites/${trackId}`, { method: "POST" }),
  removeFavorite: (trackId: string) => request<void>(`/favorites/${trackId}`, { method: "DELETE" }),
  history: () => request<SearchHistoryEntry[]>("/history"),
  register: (email: string, displayName: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, display_name: displayName, password }),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/auth/me"),
};
