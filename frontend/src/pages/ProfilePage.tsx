import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { updateCurrentUser } from "../api/auth";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { PASSWORD_REQUIRED_FOR_EMAIL, profileSchema, type ProfileForm } from "../lib/authSchemas";
import { MAX_EMAIL_LENGTH, MAX_PASSWORD_BYTES, MAX_USERNAME_LENGTH } from "../lib/fieldLimits";
import { useAuthStore } from "../stores/authStore";
import type { UserUpdatePayload } from "../types/auth";

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const {
    register,
    reset,
    watch,
    setError,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) });

  useEffect(() => {
    if (user) {
      reset({ nombre_usuario: user.nombre_usuario, correo_electronico: user.correo_electronico, password_actual: "" });
    }
  }, [reset, user]);

  const typedEmail = (watch("correo_electronico") ?? "").trim().toLowerCase();
  const emailChanges = Boolean(user && typedEmail && typedEmail !== user.correo_electronico.toLowerCase());

  async function onSubmit(values: ProfileForm) {
    setServerError(null);
    setSaved(null);
    const changesEmail = Boolean(user && values.correo_electronico !== user.correo_electronico.toLowerCase());
    if (changesEmail && !values.password_actual) {
      setError("password_actual", { message: PASSWORD_REQUIRED_FOR_EMAIL });
      return;
    }
    const payload: UserUpdatePayload = { nombre_usuario: values.nombre_usuario };
    if (changesEmail) {
      payload.correo_electronico = values.correo_electronico;
      payload.password_actual = values.password_actual;
    }
    try {
      const updated = await updateCurrentUser(payload);
      setUser(updated);
      setSaved(
        changesEmail
          ? `Te enviamos un enlace a ${values.correo_electronico}. El correo cambia cuando lo abras.`
          : "Perfil actualizado.",
      );
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo actualizar el perfil."));
    }
  }

  return (
    <div className="grid gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">cuenta // perfil</p>
        <h1 className="text-3xl font-semibold">Tu perfil</h1>
        <p className="text-terminal-muted">Actualiza tus datos de acceso y contacto.</p>
      </header>
      <Card className="max-w-2xl">
        <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
          {serverError && <Alert tone="error">{serverError}</Alert>}
          {saved && <Alert tone="success">{saved}</Alert>}
          {user?.correo_pendiente && (
            <Alert tone="info">
              Falta confirmar {user.correo_pendiente} con el enlace que te enviamos. Hasta entonces entras con{" "}
              {user.correo_electronico}.
            </Alert>
          )}
          <Input
            error={errors.nombre_usuario?.message}
            label="Nombre de usuario"
            maxLength={MAX_USERNAME_LENGTH}
            {...register("nombre_usuario")}
          />
          <Input
            error={errors.correo_electronico?.message}
            label="Correo electronico"
            maxLength={MAX_EMAIL_LENGTH}
            type="email"
            {...register("correo_electronico")}
          />
          {emailChanges && (
            <Input
              autoComplete="current-password"
              error={errors.password_actual?.message}
              label="Contraseña actual"
              maxLength={MAX_PASSWORD_BYTES}
              type="password"
              {...register("password_actual")}
            />
          )}
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? <Spinner label="Guardando" /> : "Guardar cambios"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
