/**
 * Billing constants shared by the handlers under ./handlers.
 *
 * These are policy values, not deployment configuration: changing one is a
 * product decision. Keep the tests under apps/api/test in sync.
 */

/** Days after a charge during which a customer may still request a refund. */
export const REFUND_WINDOW_DAYS = 7;

/** Business days the payment provider takes to return a refunded amount. */
export const REFUND_PAYOUT_BUSINESS_DAYS = 5;

/** Formats the invoice export endpoint can produce. */
export const SUPPORTED_EXPORT_FORMATS = ['csv'] as const;

export const MS_PER_DAY = 86_400_000;
