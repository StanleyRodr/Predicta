import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { changePassword } from "../../api/auth";
import { getApiErrorMessage } from "../../lib/apiErrors";
import { passwordChangeSchema, type PasswordChangeForm } from "../../lib/authSchemas";
import { MAX_PASSWORD_BYTES } from "../../lib/fieldLimits";
import { useAuthStore } from "../../stores/authStore";
import { Alert, Button, Card, Input, Spinner } from "../ui";

const EMPTY: PasswordChangeForm = { password_actual: "", password_nueva: "", confirmacion: "" };

/** Profile section to change the password; keeps this session with the token the API returns. */
export function PasswordChangeCard() {
  const user = useAuthStore((state) => state.user);
  const setSession = useAuthStore((state) => state.setSession);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    reset,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PasswordChangeForm>({ resolver: zodResolver(passwordChangeSchema), defaultValues: EMPTY });

  async function onSubmit(values: PasswordChangeForm) {
    setServerError(null);
    setSaved(false);
    try {
      const session = await changePassword(values.password_actual, values.password_nueva);
      // The old token stopped working; this one keeps the current session open.
      setSession(session.access_token, user);
      reset(EMPTY);
      setSaved(true);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo cambiar la contraseña."));
    }
  }

  return (
    <Card className="max-w-2xl">
      <form aria-label="Cambiar contraseña" className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
        <h2 className="text-xl font-semibold">Cambiar contraseña</h2>
        {serverError && <Alert tone="error">{serverError}</Alert>}
        {saved && (
          <Alert tone="success">Contraseña actualizada. Cerramos tus otras sesiones abiertas.</Alert>
        )}
        <Input
          autoComplete="current-password"
          error={errors.password_actual?.message}
          label="Contraseña actual"
          maxLength={MAX_PASSWORD_BYTES}
          type="password"
          {...register("password_actual")}
        />
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
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <Spinner label="Guardando" /> : "Cambiar contraseña"}
        </Button>
      </form>
    </Card>
  );
}
