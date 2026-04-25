import { clearAccessToken, getAccessToken } from "../storage/tokenStorage";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

type QueryValue = string | number | boolean | null | undefined;

type ApiErrorBody = {
  detail?: string;
};

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(path, API_BASE_URL.endsWith("/") ? API_BASE_URL : `${API_BASE_URL}/`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }

      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

export async function apiGet<T>(
  path: string,
  query?: Record<string, QueryValue>,
): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    method: "GET",
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    headers: buildHeaders({ acceptOnly: true }),
    body: formData,
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function apiPostJson<TBody extends object, TResponse>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    headers: buildHeaders({ contentType: "application/json" }),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export async function apiPatchJson<TBody extends object, TResponse>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  const response = await fetch(buildUrl(path), {
    method: "PATCH",
    headers: buildHeaders({ contentType: "application/json" }),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: "DELETE",
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

function buildHeaders(
  options: { contentType?: string; acceptOnly?: boolean } = {},
): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  const token = getAccessToken();

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.contentType && !options.acceptOnly) {
    headers["Content-Type"] = options.contentType;
  }

  return headers;
}

async function extractErrorMessage(response: Response): Promise<string> {
  if (response.status === 401) {
    clearAccessToken();
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    const body = (await response.json()) as ApiErrorBody;
    return body.detail ?? JSON.stringify(body);
  }

  return await response.text();
}
