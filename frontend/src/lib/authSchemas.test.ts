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

describe("field rules shared with the backend", () => {
  const valid = {
    nombre_usuario: "ana_maria",
    correo_electronico: "ana@example.com",
    password: "StrongPass1",
  };
  const register = (changes: Partial<typeof valid>) =>
    registerSchema.safeParse({ ...valid, ...changes });

  it.each(["ana", "Ana María", "josé.pérez-2", "user_01", "x".repeat(50)])(
    "accepts the username %s",
    (nombre) => {
      expect(register({ nombre_usuario: nombre }).success).toBe(true);
    },
  );

  it.each(["ab", "x".repeat(51), "ana<script>", "ana;drop", "a@b", "   "])(
    "rejects the username %s",
    (nombre) => {
      expect(register({ nombre_usuario: nombre }).success).toBe(false);
    },
  );

  it("trims the username and lowercases the email", () => {
    const result = register({ nombre_usuario: "  ana  ", correo_electronico: " Ana@Example.COM " });
    expect(result.success).toBe(true);
    expect(result.data).toMatchObject({ nombre_usuario: "ana", correo_electronico: "ana@example.com" });
  });

  it("rejects an email over 100 characters", () => {
    expect(register({ correo_electronico: `${"a".repeat(64)}@${"b".repeat(40)}.com` }).success).toBe(
      false,
    );
  });

  it("limits the password to 72 bytes, counting accents as 2", () => {
    expect(register({ password: `Aa1${"x".repeat(69)}` }).success).toBe(true);
    expect(register({ password: `Aa1${"x".repeat(70)}` }).success).toBe(false);
    expect(register({ password: `Aa1${"ñ".repeat(35)}` }).success).toBe(false);
  });

  it("rejects control characters in the password", () => {
    expect(register({ password: "Tab\tPass1x" }).success).toBe(false);
  });

  it("rejects a login password over 72 bytes", () => {
    expect(
      loginSchema.safeParse({ correo_electronico: "ana@example.com", password: "x".repeat(73) })
        .success,
    ).toBe(false);
  });

  it("applies the username rule to the profile", () => {
    expect(profileSchema.safeParse({ nombre_usuario: "a<b>c", correo_electronico: "a@b.com" }).success).toBe(
      false,
    );
  });
});
