import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { resetPassword } from "../api/auth";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { resetPasswordSchema, type ResetPasswordForm } from "../lib/authSchemas";
import { MAX_PASSWORD_BYTES } from "../lib/fieldLimits";
import { MISSING_TOKEN, useLinkToken } from "../lib/linkToken";

export function ResetPasswordPage() {
  const token = useLinkToken();
  const [done, setDone] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordForm>({ resolver: zodResolver(resetPasswordSchema) });

  async function onSubmit(values: ResetPasswordForm) {
    if (!token) return;
    setServerError(null);
    try {
      setDone((await resetPassword(token, values.password_nueva)).message);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo cambiar la contraseña."));
    }
  }

  const loginLink = (
    <p className="text-center text-sm text-terminal-muted">
      <Link className="text-terminal-amber hover:underline" to="/login">
        Ir a iniciar sesión
      </Link>
    </p>
  );

  return (
    <AuthLayout description="Al guardarla se cierran todas tus sesiones." title="Elige una contraseña nueva">
      <Card>
        {!token ? (
          <div className="grid gap-5">
            <Alert tone="error">{MISSING_TOKEN}</Alert>
            {loginLink}
          </div>
        ) : done ? (
          <div className="grid gap-5">
            <Alert tone="success">{done}</Alert>
            {loginLink}
          </div>
        ) : (
          <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
            {serverError && <Alert tone="error">{serverError}</Alert>}
            <Input
              autoComplete="new-password"
              error={errors.password_nueva?.message}
              label="Contraseña nueva"
              maxLength={MAX_PASSWORD_BYTES}
              type="password"
              {...register("password_nueva")}
            />
            <Input
              autoComplete="new-password"
              error={errors.confirmacion?.message}
              label="Repite la contraseña nueva"
              maxLength={MAX_PASSWORD_BYTES}
              type="password"
              {...register("confirmacion")}
            />
            <p className="text-xs leading-5 text-terminal-muted">
              Minimo 8 caracteres, una mayuscula, una minuscula y un digito.
            </p>
            <Button disabled={isSubmitting} type="submit">
              {isSubmitting ? <Spinner label="Guardando" /> : "Guardar contraseña"}
            </Button>
          </form>
        )}
      </Card>
    </AuthLayout>
  );
}
