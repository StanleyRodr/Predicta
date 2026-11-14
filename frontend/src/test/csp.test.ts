import { describe, expect, it } from "vitest";
import { connectOrigin, contentSecurityPolicy, headerPolicy, injectCsp, originOf } from "../../csp";
import vercel from "../../vercel.json";

function vercelHeader(key: string): string | undefined {
  return vercel.headers.flatMap((rule) => rule.headers).find((header) => header.key === key)?.value;
}

describe("content security policy", () => {
  it("allows only the API origin besides the site itself", () => {
    const policy = contentSecurityPolicy("https://api.ejemplo.com");

    expect(policy).toContain("connect-src 'self' https://api.ejemplo.com");
    expect(policy).toContain("script-src 'self'");
    expect(policy).toContain("object-src 'none'");
    expect(policy).not.toContain("unsafe-eval");
    expect(policy).not.toContain("unsafe-inline");
  });

  it("takes the origin of the API URL, without its path", () => {
    expect(originOf("https://api.ejemplo.com/v1/")).toBe("https://api.ejemplo.com");
    expect(originOf("http://localhost:8000")).toBe("http://localhost:8000");
  });

  it("injects the policy first in the head", () => {
    const html = injectCsp("<html><head><title>x</title></head></html>", "https://api.ejemplo.com");

    expect(html).toMatch(/<head>\s*<meta http-equiv="Content-Security-Policy" content="[^"]+https:\/\/api\.ejemplo\.com/);
    expect(html.indexOf("Content-Security-Policy")).toBeLessThan(html.indexOf("<title>"));
  });

  it("keeps the vercel.json header equal to the meta policy plus frame-ancestors", () => {
    const header = vercelHeader("Content-Security-Policy");
    const origin = header ? connectOrigin(header) : null;

    expect(origin).toMatch(/^https:\/\//);
    expect(header).toBe(headerPolicy(origin as string));
  });

  it("sends the headers a meta cannot set", () => {
    expect(vercelHeader("Strict-Transport-Security")).toBe("max-age=31536000; includeSubDomains");
    expect(vercelHeader("X-Content-Type-Options")).toBe("nosniff");
    expect(vercelHeader("Referrer-Policy")).toBe("no-referrer");
    expect(vercelHeader("Permissions-Policy")).toContain("camera=()");
  });

  it("serves the SPA for the links that arrive by e-mail", () => {
    const rewrite = vercel.rewrites[0];
    const pattern = new RegExp(`^${rewrite.source.replace("(.*)", "(.*)")}$`);

    expect(rewrite.destination).toBe("/index.html");
    for (const path of ["/verificar-correo", "/restablecer-contrasena", "/olvide-contrasena", "/dashboard"]) {
      expect(pattern.test(path)).toBe(true);
    }
  });
});
