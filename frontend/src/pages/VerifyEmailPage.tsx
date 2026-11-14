import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { confirmEmail } from "../api/auth";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Alert, Card, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { MISSING_TOKEN, useLinkToken } from "../lib/linkToken";

type Result = { tone: "success" | "error"; message: string };

export function VerifyEmailPage() {
  const token = useLinkToken();
  const [result, setResult] = useState<Result | null>(
    token ? null : { tone: "error", message: MISSING_TOKEN },
  );
  // A token works once: StrictMode must not send it twice.
  const sent = useRef(false);

  useEffect(() => {
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
