import { z } from "zod";
import {
  CONTROL_CHARACTERS,
  MAX_EMAIL_LENGTH,
  MAX_PASSWORD_BYTES,
  MAX_USERNAME_LENGTH,
  MIN_PASSWORD_LENGTH,
  MIN_USERNAME_LENGTH,
  USERNAME_PATTERN,
  utf8Length,
} from "./fieldLimits";

const PASSWORD_TOO_LONG = `La contraseña no puede superar ${MAX_PASSWORD_BYTES} bytes (las letras con tilde ocupan 2).`;

const emailSchema = z
  .string()
  .trim()
  .toLowerCase()
  .max(MAX_EMAIL_LENGTH, `Usa como maximo ${MAX_EMAIL_LENGTH} caracteres.`)
  .pipe(z.email("Escribe un correo valido."));

const usernameSchema = z
  .string()
  .trim()
  .min(MIN_USERNAME_LENGTH, `Usa al menos ${MIN_USERNAME_LENGTH} caracteres.`)
  .max(MAX_USERNAME_LENGTH, `Usa como maximo ${MAX_USERNAME_LENGTH} caracteres.`)
  .regex(USERNAME_PATTERN, "Usa solo letras, digitos, espacios, punto, guion y guion bajo.");

const passwordSchema = z
  .string()
  .min(MIN_PASSWORD_LENGTH, `Usa al menos ${MIN_PASSWORD_LENGTH} caracteres.`)
  .refine((value) => utf8Length(value) <= MAX_PASSWORD_BYTES, PASSWORD_TOO_LONG)
  .refine((value) => !CONTROL_CHARACTERS.test(value), "La contraseña tiene caracteres no permitidos.")
  .regex(/[a-z]/, "Incluye una letra minuscula.")
  .regex(/[A-Z]/, "Incluye una letra mayuscula.")
  .regex(/\d/, "Incluye un digito.");

export const loginSchema = z.object({
  correo_electronico: emailSchema,
  password: z
    .string()
    .min(1, "Escribe tu contraseña.")
    .refine((value) => utf8Length(value) <= MAX_PASSWORD_BYTES, PASSWORD_TOO_LONG),
});

export const registerSchema = z.object({
  nombre_usuario: usernameSchema,
  correo_electronico: emailSchema,
  password: passwordSchema,
});

export const PASSWORD_REQUIRED_FOR_EMAIL = "Escribe tu contraseña actual para cambiar el correo.";

export const profileSchema = z.object({
  nombre_usuario: usernameSchema,
  correo_electronico: emailSchema,
  // Only needed when the e-mail changes; ProfilePage enforces that case.
  password_actual: z
    .string()
    .refine((value) => utf8Length(value) <= MAX_PASSWORD_BYTES, PASSWORD_TOO_LONG)
    .optional(),
});

const PASSWORDS_DIFFER = "Las contraseñas no coinciden.";

const currentPasswordSchema = z
  .string()
  .min(1, "Escribe tu contraseña actual.")
  .refine((value) => utf8Length(value) <= MAX_PASSWORD_BYTES, PASSWORD_TOO_LONG);

export const passwordChangeSchema = z
  .object({
    password_actual: currentPasswordSchema,
    password_nueva: passwordSchema,
    confirmacion: z.string(),
  })
  .refine((values) => values.password_nueva === values.confirmacion, {
    message: PASSWORDS_DIFFER,
    path: ["confirmacion"],
  })
  .refine((values) => values.password_nueva !== values.password_actual, {
    message: "La contraseña nueva debe ser distinta de la actual.",
    path: ["password_nueva"],
  });

export const forgotPasswordSchema = z.object({ correo_electronico: emailSchema });

export const resetPasswordSchema = z
  .object({ password_nueva: passwordSchema, confirmacion: z.string() })
  .refine((values) => values.password_nueva === values.confirmacion, {
    message: PASSWORDS_DIFFER,
    path: ["confirmacion"],
  });

export type LoginForm = z.infer<typeof loginSchema>;
export type PasswordChangeForm = z.infer<typeof passwordChangeSchema>;
export type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;
export type RegisterForm = z.infer<typeof registerSchema>;
export type ProfileForm = z.infer<typeof profileSchema>;
