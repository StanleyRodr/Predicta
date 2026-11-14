import type { AxiosResponse } from "axios";
import { http } from "./http";
import type { LoginResponse, User } from "../types/api";
import type { MessageResponse, RegisterPayload, UserUpdatePayload } from "../types/auth";

export async function registerUser(payload: RegisterPayload): Promise<User> {
  const response = await http.post<User>("/users/register", payload);
  return response.data;
}

export async function loginUser(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const body = new URLSearchParams({ username: email, password });
  const response = await http.post<LoginResponse>("/users/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await http.get<User>("/users/me");
  return response.data;
}

export async function updateCurrentUser(payload: UserUpdatePayload): Promise<User> {
  const response: AxiosResponse<User> = await http.put("/users/me", payload);
  return response.data;
}

/** Ask for a new verification link; the answer is the same whether the account exists or not. */
export async function resendVerification(correo_electronico: string): Promise<MessageResponse> {
  const response = await http.post<MessageResponse>("/users/verificacion/reenviar", { correo_electronico });
  return response.data;
}

/** Confirm the address of an e-mailed link with its token. */
export async function confirmEmail(token: string): Promise<MessageResponse> {
  const response = await http.post<MessageResponse>("/users/verificacion/confirmar", { token });
  return response.data;
}

/** Change the password with the current one; the answer carries the new session token. */
export async function changePassword(password_actual: string, password_nueva: string): Promise<LoginResponse> {
  const response = await http.put<LoginResponse>("/users/me/password", { password_actual, password_nueva });
  return response.data;
}

/** Ask for a reset link; the answer is the same whether the account exists or not. */
export async function forgotPassword(correo_electronico: string): Promise<MessageResponse> {
  const response = await http.post<MessageResponse>("/users/contrasena/olvido", { correo_electronico });
  return response.data;
}

/** Set a new password with the token of a reset link. */
export async function resetPassword(token: string, password_nueva: string): Promise<MessageResponse> {
  const response = await http.post<MessageResponse>("/users/contrasena/restablecer", { token, password_nueva });
  return response.data;
}
