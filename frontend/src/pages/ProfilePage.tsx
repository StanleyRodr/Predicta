import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { updateCurrentUser } from "../api/auth";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { profileSchema, type ProfileForm } from "../lib/authSchemas";
import { useAuthStore } from "../stores/authStore";

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    reset,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) });

  useEffect(() => {
    if (user) reset({ nombre_usuario: user.nombre_usuario, correo_electronico: user.correo_electronico });
  }, [reset, user]);

  async function onSubmit(values: ProfileForm) {
    setServerError(null);
    setSaved(false);
    try {
      const updated = await updateCurrentUser(values);
      setUser(updated);
      setSaved(true);
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
          {saved && <Alert tone="success">Perfil actualizado.</Alert>}
          <Input error={errors.nombre_usuario?.message} label="Nombre de usuario" {...register("nombre_usuario")} />
          <Input
            error={errors.correo_electronico?.message}
            label="Correo electronico"
            type="email"
            {...register("correo_electronico")}
          />
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? <Spinner label="Guardando" /> : "Guardar cambios"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
