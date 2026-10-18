import { z } from "zod";

const passwordSchema = z
  .string()
  .min(8, "Usa al menos 8 caracteres.")
  .regex(/[a-z]/, "Incluye una letra minuscula.")
  .regex(/[A-Z]/, "Incluye una letra mayuscula.")
  .regex(/\d/, "Incluye un digito.");

export const loginSchema = z.object({
  correo_electronico: z.email("Escribe un correo valido."),
  password: z.string().min(1, "Escribe tu contraseña."),
});

export const registerSchema = z.object({
  nombre_usuario: z.string().min(3, "Usa al menos 3 caracteres."),
  correo_electronico: z.email("Escribe un correo valido."),
  password: passwordSchema,
});

export const profileSchema = z.object({
  nombre_usuario: z.string().min(3, "Usa al menos 3 caracteres."),
  correo_electronico: z.email("Escribe un correo valido."),
});

export type LoginForm = z.infer<typeof loginSchema>;
export type RegisterForm = z.infer<typeof registerSchema>;
export type ProfileForm = z.infer<typeof profileSchema>;
