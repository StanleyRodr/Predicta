/**
 * Field limits shared with the backend (`backend/app/schemas/schemas.py`).
 * `backend/tests/test_field_limits_contract.py` fails if the two disagree.
 */
export const MIN_USERNAME_LENGTH = 3;
export const MAX_USERNAME_LENGTH = 50;
export const MAX_EMAIL_LENGTH = 100;
export const MIN_PASSWORD_LENGTH = 8;
export const MAX_PASSWORD_BYTES = 72;
export const MAX_CATEGORY_LENGTH = 100;
export const MAX_PRODUCT_LENGTH = 150;

/** Letters (accented included), digits, space, dot, hyphen and underscore. */
export const USERNAME_PATTERN = /^[\p{L}\p{N} ._-]+$/u;
// eslint-disable-next-line no-control-regex -- the rule is precisely about control characters
export const CONTROL_CHARACTERS = /[\x00-\x1f\x7f]/;

/** Length of a text in UTF-8 bytes, the unit bcrypt limits. */
export function utf8Length(value: string): number {
  return new TextEncoder().encode(value).length;
}
