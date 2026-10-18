import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth";
import { AuthLayout } from "../components/auth/AuthLayout";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { registerSchema, type RegisterForm } from "../lib/authSchemas";

export function RegisterPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterForm) {
    setServerError(null);
    setIsSubmitting(true);
    try {
      await registerUser(values);
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo crear la cuenta."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout description="Crea tu espacio privado de analisis." title="Crear cuenta">
      <Card>
        <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
          {serverError && <Alert tone="error">{serverError}</Alert>}
          <Input
            autoComplete="username"
            error={errors.nombre_usuario?.message}
            label="Nombre de usuario"
            {...register("nombre_usuario")}
          />
          <Input
            autoComplete="email"
            error={errors.correo_electronico?.message}
            label="Correo electronico"
            type="email"
            {...register("correo_electronico")}
          />
          <Input
            autoComplete="new-password"
            error={errors.password?.message}
            label="Contraseña"
            type="password"
            {...register("password")}
          />
          <p className="text-xs leading-5 text-terminal-muted">
            Minimo 8 caracteres, una mayuscula, una minuscula y un digito.
          </p>
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? <Spinner label="Creando cuenta" /> : "Crear cuenta"}
          </Button>
          <p className="text-center text-sm text-terminal-muted">
            ¿Ya tienes cuenta?{" "}
            <Link className="text-terminal-amber hover:underline" to="/login">
              Entra aqui
            </Link>
          </p>
        </form>
      </Card>
    </AuthLayout>
  );
}
