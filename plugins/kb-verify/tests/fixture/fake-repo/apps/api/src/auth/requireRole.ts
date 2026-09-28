import { ApiError } from '../errors';
import type { Role, User } from '../types';

/**
 * Throws FORBIDDEN unless the user's role is one of `allowed`.
 * Handlers call this first, before touching the database.
 */
export function requireRole(user: User, allowed: Role[]): void {
  if (!allowed.includes(user.role)) {
    throw new ApiError('FORBIDDEN');
  }
}
