/** Shared auth form validators — any valid email domain is accepted. */

const EMAIL_RE =
  /^(?!\.)(?!.*\.\.)[A-Za-z0-9._%+\-]+@[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?)+$/;

export const MIN_PASSWORD_LENGTH = 8;

export function isValidEmail(email) {
  return EMAIL_RE.test((email || '').trim());
}

export function emailError(email) {
  const value = (email || '').trim();
  if (!value) return 'Please enter your email address.';
  if (!isValidEmail(value)) {
    return 'Enter a valid email address, e.g. name@gmail.com or name@university.edu.';
  }
  return '';
}

export function passwordError(password, { requiredMessage = 'Please enter a password.' } = {}) {
  if (!password) return requiredMessage;
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return 'Password must include at least one letter and one number.';
  }
  return '';
}
