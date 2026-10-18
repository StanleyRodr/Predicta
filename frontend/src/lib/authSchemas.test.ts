import { describe, expect, it } from "vitest";
import { loginSchema, profileSchema, registerSchema } from "./authSchemas";

describe("auth schemas", () => {
  it("accepts valid login and registration data", () => {
    expect(
      loginSchema.safeParse({ correo_electronico: "ana@example.com", password: "Secret1" })
        .success,
    ).toBe(true);
    expect(
      registerSchema.safeParse({
        nombre_usuario: "ana",
        correo_electronico: "ana@example.com",
        password: "Secret1a",
      }).success,
    ).toBe(true);
  });

  it("rejects weak password, invalid email, and short profile name", () => {
    expect(
      registerSchema.safeParse({
        nombre_usuario: "ana",
        correo_electronico: "not-an-email",
        password: "weak",
      }).success,
    ).toBe(false);
    expect(profileSchema.safeParse({ nombre_usuario: "ab", correo_electronico: "a@b.com" }).success).toBe(
      false,
    );
  });
});
