import { useEffect, useState } from "react";
import { getJson } from "./api";

export interface Loaded<T> {
  /** undefined while loading, null when the backend has no such record */
  data: T | null | undefined;
  failed: boolean;
  reload: () => void;
}

export function useApi<T>(path: string, every?: number): Loaded<T> {
  const [state, setState] = useState<{
    data: T | null | undefined;
    failed: boolean;
  }>({ data: undefined, failed: false });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let live = true;
    const load = () => {
      getJson<T>(path).then(
        (data) => {
          if (live) setState({ data, failed: false });
        },
        () => {
          if (live) setState((previous) => ({ ...previous, failed: true }));
        },
      );
    };
    load();
    const timer =
      every === undefined ? undefined : window.setInterval(load, every);
    return () => {
      live = false;
      window.clearInterval(timer);
    };
  }, [path, every, version]);

  return {
    ...state,
    reload: () => {
      setVersion((v) => v + 1);
    },
  };
}
