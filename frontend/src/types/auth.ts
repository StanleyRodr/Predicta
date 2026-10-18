import type { User } from "./api";

export interface RegisterPayload {
  nombre_usuario: string;
  correo_electronico: string;
  password: string;
}

export interface UserUpdatePayload {
  nombre_usuario?: string;
  correo_electronico?: string;
}

export type AuthUser = User;
