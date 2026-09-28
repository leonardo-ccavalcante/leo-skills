/**
 * Error catalog.
 *
 * Codes are stable identifiers shared with the front end, which maps them to
 * user-facing text under `billing.errors.<CODE>` in apps/web/locales. The
 * messages below are for logs and API clients; never show them to users.
 */
export const ERROR_CATALOG = {
  FORBIDDEN: {
    status: 403,
    message: 'The current role is not allowed to perform this action.',
  },
  SUB_NOT_FOUND: {
    status: 404,
    message: 'Subscription not found.',
  },
  SUB_ALREADY_CANCELLED: {
    status: 409,
    message: 'The subscription is already cancelled or scheduled to cancel.',
  },
  CHARGE_NOT_FOUND: {
    status: 404,
    message: 'Charge not found.',
  },
  REFUND_WINDOW_EXPIRED: {
    status: 422,
    message: 'The refund window for this charge has closed.',
  },
  REFUND_ALREADY_REQUESTED: {
    status: 409,
    message: 'A refund was already requested for this charge.',
  },
  PLAN_UNKNOWN: {
    status: 422,
    message: 'Unknown plan.',
  },
  PLAN_SEAT_LIMIT_EXCEEDED: {
    status: 422,
    message: 'The workspace has more members than the target plan allows.',
  },
} as const;

export type ErrorCode = keyof typeof ERROR_CATALOG;

export class ApiError extends Error {
  readonly code: ErrorCode;
  readonly status: number;

  constructor(code: ErrorCode) {
    super(ERROR_CATALOG[code].message);
    this.name = 'ApiError';
    this.code = code;
    this.status = ERROR_CATALOG[code].status;
  }

  toJSON() {
    return { code: this.code, message: this.message };
  }
}
