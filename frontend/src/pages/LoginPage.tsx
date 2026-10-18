import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { loginUser, getCurrentUser } from "../api/auth";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { AuthLayout } from "../components/auth/AuthLayout";
import { getApiErrorMessage } from "../lib/apiErrors";
import { loginSchema, type LoginForm } from "../lib/authSchemas";
import { useAuthStore } from "../stores/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
  const destination = from && from !== "/login" ? from : "/dashboard";
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginForm) {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const session = await loginUser(values.correo_electronico, values.password);
      setSession(session.access_token, null);
      const user = await getCurrentUser();
      setSession(session.access_token, user);
      navigate(destination, { replace: true });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo iniciar sesion."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout description="Accede a tus ventas, metricas y proyecciones." title="Entrar a Predicta">
      <Card>
        <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
          {serverError && <Alert tone="error">{serverError}</Alert>}
          <Input
            autoComplete="email"
            error={errors.correo_electronico?.message}
            label="Correo electronico"
            type="email"
            {...register("correo_electronico")}
          />
          <Input
            autoComplete="current-password"
            error={errors.password?.message}
            label="Contraseña"
            type="password"
            {...register("password")}
          />
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? <Spinner label="Entrando" /> : "Entrar"}
          </Button>
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
