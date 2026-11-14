export interface User {
  id_usuario: number;
  nombre_usuario: string;
  correo_electronico: string;
  id_rol: number | null;
  fecha_registro: string;
  correo_verificado: boolean;
  /** New address waiting for its link; it replaces correo_electronico once confirmed. */
  correo_pendiente: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
}
