import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useAuthStore } from "../../stores/authStore";

// Watching the token covers manual logout, 401 responses, and failed session
// checks. A first login is skipped so it cannot drop the queries it just started.
export function SessionCacheGuard() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token);
  const previousToken = useRef(token);

  useEffect(() => {
    if (previousToken.current && previousToken.current !== token) {
      queryClient.clear();
    }
    previousToken.current = token;
  }, [queryClient, token]);

  return null;
}
