import { useEffect, useState } from "react";

export const MISSING_TOKEN = "El enlace está incompleto. Ábrelo tal como llegó a tu correo.";

/** Token of an e-mailed link: ``#token=...``. The fragment never reaches the server or the Referer. */
export function readLinkToken(): string | null {
  return new URLSearchParams(window.location.hash.slice(1)).get("token");
}

/** Read the link token once and drop the fragment from the address bar. */
export function useLinkToken(): string | null {
  const [token] = useState(readLinkToken);
  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }, []);
  return token;
}
