import { env } from "@/config/env";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  /** When true, a 401 will not invoke the global unauthorized handler. */
  suppressUnauthorized?: boolean;
};

let onUnauthorized: (() => void) | null = null;

/** Register a handler invoked on any 401 response (wired in F2 auth). */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

function resolveUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${env.apiUrl}${normalized}`;
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map(String).join(", ");
  }
  return fallback;
}

export async function apiClient<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, suppressUnauthorized, ...rest } = options;

  const response = await fetch(resolveUrl(path), {
    ...rest,
    credentials: "include",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    if (!suppressUnauthorized) {
      onUnauthorized?.();
    }
    throw new ApiError(401, "Unauthorized");
  }

  if (!response.ok) {
    let errorBody: unknown;
    const contentType = response.headers.get("content-type");
    if (contentType?.includes("application/json")) {
      errorBody = await response.json();
    } else {
      errorBody = await response.text();
    }
    throw new ApiError(
      response.status,
      extractErrorMessage(errorBody, response.statusText),
      errorBody,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json() as Promise<T>;
  }

  return response.text() as Promise<T>;
}
