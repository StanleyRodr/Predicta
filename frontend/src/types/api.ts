export interface User {
  id_usuario: number;
  nombre_usuario: string;
  correo_electronico: string;
  id_rol: number | null;
  fecha_registro: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
}
