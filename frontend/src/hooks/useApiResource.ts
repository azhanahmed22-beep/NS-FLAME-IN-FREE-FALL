import { useCallback, useEffect, useState } from "react";
import { ApiFailure, getApi } from "../services/api";

export interface ApiResource<T> {
  data: T | null;
  error: ApiFailure | null;
  loading: boolean;
  reload: () => void;
}

export function useApiResource<T>(path: string): ApiResource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiFailure | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getApi<T>(path)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setData(null);
          setError(
            cause instanceof ApiFailure
              ? cause
              : new ApiFailure(`Request failed for ${path}.`, "request-failed"),
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [path, attempt]);

  return { data, error, loading, reload };
}
