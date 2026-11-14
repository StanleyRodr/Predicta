import type { User } from "./api";

export interface RegisterPayload {
  nombre_usuario: string;
  correo_electronico: string;
  password: string;
}

export interface UserUpdatePayload {
  nombre_usuario?: string;
  correo_electronico?: string;
  /** Required when correo_electronico changes. */
  password_actual?: string;
}

export interface MessageResponse {
  message: string;
}

export type AuthUser = User;
