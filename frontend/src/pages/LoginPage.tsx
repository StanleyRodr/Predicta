import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { getCurrentUser, loginUser, resendVerification } from "../api/auth";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { AuthLayout } from "../components/auth/AuthLayout";
import { getApiErrorMessage } from "../lib/apiErrors";
import { loginSchema, type LoginForm } from "../lib/authSchemas";
import { MAX_EMAIL_LENGTH, MAX_PASSWORD_BYTES } from "../lib/fieldLimits";
import { useAuthStore } from "../stores/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Set after a 403: the password was right but the e-mail is not confirmed yet.
  const [unverifiedEmail, setUnverifiedEmail] = useState<string | null>(null);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
  const destination = from && from !== "/login" ? from : "/dashboard";
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginForm) {
    setServerError(null);
    setUnverifiedEmail(null);
    setResendMessage(null);
    setIsSubmitting(true);
    try {
      const session = await loginUser(values.correo_electronico, values.password);
      setSession(session.access_token, null);
      const user = await getCurrentUser();
      setSession(session.access_token, user);
      navigate(destination, { replace: true });
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 403) {
        setUnverifiedEmail(values.correo_electronico);
      }
      setServerError(getApiErrorMessage(error, "No se pudo iniciar sesion."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onResend() {
    if (!unverifiedEmail) return;
    setIsResending(true);
    try {
      const response = await resendVerification(unverifiedEmail);
      setResendMessage(response.message);
    } catch (error) {
      setResendMessage(getApiErrorMessage(error, "No se pudo reenviar el enlace."));
    } finally {
      setIsResending(false);
    }
  }

  return (
    <AuthLayout description="Accede a tus ventas, metricas y proyecciones." title="Entrar a Predicta">
      <Card>
        <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
          {serverError && <Alert tone="error">{serverError}</Alert>}
          {unverifiedEmail && (
            <Button disabled={isResending} onClick={onResend} type="button" variant="secondary">
              {isResending ? <Spinner label="Reenviando" /> : "Reenviar enlace"}
            </Button>
          )}
          {resendMessage && <Alert tone="info">{resendMessage}</Alert>}
          <Input
            autoComplete="email"
            error={errors.correo_electronico?.message}
            label="Correo electronico"
            maxLength={MAX_EMAIL_LENGTH}
            type="email"
            {...register("correo_electronico")}
          />
          <Input
            autoComplete="current-password"
            error={errors.password?.message}
            label="Contraseña"
            maxLength={MAX_PASSWORD_BYTES}
            type="password"
            {...register("password")}
          />
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? <Spinner label="Entrando" /> : "Entrar"}
          </Button>
          <p className="text-center text-sm">
            <Link className="text-terminal-amber hover:underline" to="/olvide-contrasena">
              ¿Olvidaste tu contraseña?
            </Link>
          </p>
          <p className="text-center text-sm text-terminal-muted">
            ¿Primera vez aqui?{" "}
            <Link className="text-terminal-amber hover:underline" to="/register">
              Crea tu cuenta
            </Link>
          </p>
        </form>
      </Card>
    </AuthLayout>
  );
}
