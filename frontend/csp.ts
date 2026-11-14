/**
 * Content Security Policy of the SPA: the single source for the `<meta>` the
 * build injects (vite.config.ts) and for the header in vercel.json, which a
 * test keeps equal. No Node imports: the app tests import this file too.
 */

/** Scheme, host and port of the API, as CSP `connect-src` needs it. */
export function originOf(url: string): string {
  const match = /^(https?:\/\/[^/?#]+)/i.exec(url.trim());
  if (!match) throw new Error(`VITE_API_URL no es una URL http(s): ${url}`);
  return match[1].toLowerCase();
}

/** The policy for an API at `apiOrigin`. `frame-ancestors` only works as a header. */
export function contentSecurityPolicy(apiOrigin: string): string {
  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src 'self' ${apiOrigin}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

/** The vercel.json header: the `<meta>` policy plus what a `<meta>` cannot carry. */
export function headerPolicy(apiOrigin: string): string {
  return `${contentSecurityPolicy(apiOrigin)}; frame-ancestors 'none'`;
}

/** Put the `<meta>` first in `<head>`, so it applies before any other resource loads. */
export function injectCsp(html: string, apiOrigin: string): string {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${contentSecurityPolicy(apiOrigin)}" />`;
  return html.replace("<head>", `<head>\n    ${meta}`);
}

/** The API origin written in the `connect-src` of a policy. */
export function connectOrigin(policy: string): string | null {
  const directive = policy.split(";").map((part) => part.trim()).find((part) => part.startsWith("connect-src "));
  const origin = directive?.split(/\s+/).find((source) => /^https?:\/\//.test(source));
  return origin ?? null;
}
