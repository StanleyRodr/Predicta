import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { confirmEmail } from "../api/auth";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Alert, Card, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";

export const MISSING_TOKEN = "El enlace está incompleto. Ábrelo tal como llegó a tu correo.";

/** Token from the link fragment (#token=...), which never reaches the server or the Referer. */
function readToken(): string | null {
  const params = new URLSearchParams(window.location.hash.slice(1));
  return params.get("token");
}

type Result = { tone: "success" | "error"; message: string };

export function VerifyEmailPage() {
  const [token] = useState(readToken);
  const [result, setResult] = useState<Result | null>(
    token ? null : { tone: "error", message: MISSING_TOKEN },
  );
  // A token works once: StrictMode must not send it twice.
  const sent = useRef(false);

  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
    if (!token || sent.current) return;
    sent.current = true;
    confirmEmail(token)
      .then((response) => setResult({ tone: "success", message: response.message }))
      .catch((error: unknown) =>
        setResult({ tone: "error", message: getApiErrorMessage(error, "No se pudo confirmar el correo.") }),
      );
  }, [token]);

  return (
    <AuthLayout description="Confirmamos que el correo es tuyo." title="Verificar correo">
      <Card>
        <div className="grid gap-5">
          {result ? (
            <Alert tone={result.tone}>{result.message}</Alert>
          ) : (
            <Spinner label="Confirmando tu correo" />
          )}
          {result && (
            <p className="text-center text-sm text-terminal-muted">
              <Link className="text-terminal-amber hover:underline" to="/login">
                Ir a iniciar sesión
              </Link>
            </p>
          )}
        </div>
      </Card>
    </AuthLayout>
  );
}
