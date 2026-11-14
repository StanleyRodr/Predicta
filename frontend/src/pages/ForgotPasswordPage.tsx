import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/auth";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { forgotPasswordSchema, type ForgotPasswordForm } from "../lib/authSchemas";
import { MAX_EMAIL_LENGTH } from "../lib/fieldLimits";

export function ForgotPasswordPage() {
  const [answer, setAnswer] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordForm>({ resolver: zodResolver(forgotPasswordSchema) });

  async function onSubmit(values: ForgotPasswordForm) {
    setServerError(null);
    try {
      // The backend answers the same whether the account exists or not.
      setAnswer((await forgotPassword(values.correo_electronico)).message);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo enviar el enlace."));
    }
  }

  return (
    <AuthLayout description="Te enviamos un enlace para elegir una contraseña nueva." title="Olvidé mi contraseña">
      <Card>
        {answer ? (
          <div className="grid gap-5">
            <Alert tone="success">{answer}</Alert>
            <p className="text-center text-sm text-terminal-muted">
              El enlace vence en 30 minutos.{" "}
              <Link className="text-terminal-amber hover:underline" to="/login">
                Volver a iniciar sesión
              </Link>
            </p>
          </div>
        ) : (
          <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
            {serverError && <Alert tone="error">{serverError}</Alert>}
            <Input
              autoComplete="email"
              error={errors.correo_electronico?.message}
              label="Correo electronico"
              maxLength={MAX_EMAIL_LENGTH}
              type="email"
              {...register("correo_electronico")}
            />
            <Button disabled={isSubmitting} type="submit">
              {isSubmitting ? <Spinner label="Enviando" /> : "Enviar enlace"}
            </Button>
            <p className="text-center text-sm text-terminal-muted">
              <Link className="text-terminal-amber hover:underline" to="/login">
                Volver a iniciar sesión
              </Link>
            </p>
          </form>
        )}
      </Card>
    </AuthLayout>
  );
}
