import axios, { AxiosError } from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 12_000,
  headers: { Accept: "application/json" },
});

interface OpenApiDocument {
  paths?: Record<string, { get?: unknown; post?: unknown }>;
}

let openApiDocument: Promise<OpenApiDocument> | null = null;

export type ApiFailureKind = "offline" | "not-implemented" | "request-failed";

export class ApiFailure extends Error {
  constructor(
    message: string,
    readonly kind: ApiFailureKind,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiFailure";
  }
}

export async function getApi<T>(path: string): Promise<T> {
  try {
    await assertRouteExists(path, "get");
    const response = await api.get<T>(path);
    return response.data;
  } catch (error) {
    if (error instanceof ApiFailure) throw error;
    throw toApiFailure(error, path);
  }
}

export async function postApi<T>(path: string, payload: unknown): Promise<T> {
  try {
    await assertRouteExists(path, "post");
    const response = await api.post<T>(path, payload);
    return response.data;
  } catch (error) {
    if (error instanceof ApiFailure) throw error;
    throw toApiFailure(error, path);
  }
}

async function assertRouteExists(path: string, method: "get" | "post"): Promise<void> {
  if (!openApiDocument) {
    openApiDocument = api.get<OpenApiDocument>("/openapi.json")
      .then((response) => response.data)
      .catch((error: unknown) => {
        openApiDocument = null;
        throw toApiFailure(error, "/openapi.json");
      });
  }

  const document = await openApiDocument;
  if (!document.paths?.[path]?.[method]) {
    throw new ApiFailure(
      `${method.toUpperCase()} ${path} is not implemented by the connected backend yet.`,
      "not-implemented",
      404,
    );
  }
}

function toApiFailure(error: unknown, path: string): ApiFailure {
  if (error instanceof ApiFailure) return error;
  if (!axios.isAxiosError(error)) {
    return new ApiFailure(`Could not complete the request to ${path}.`, "request-failed");
  }

  const axiosError = error as AxiosError;
  if (!axiosError.response) {
    return new ApiFailure(
      `The API at ${api.defaults.baseURL} could not be reached. Check the backend and VITE_API_BASE_URL.`,
      "offline",
    );
  }

  if (axiosError.response.status === 404 || axiosError.response.status === 405) {
    return new ApiFailure(
      `${path} is not implemented by the connected backend yet.`,
      "not-implemented",
      axiosError.response.status,
    );
  }

  return new ApiFailure(
    `The API returned HTTP ${axiosError.response.status} for ${path}.`,
    "request-failed",
    axiosError.response.status,
  );
}
