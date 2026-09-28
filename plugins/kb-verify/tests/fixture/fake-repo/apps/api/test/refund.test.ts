import { describe, expect, it } from 'vitest';
import { REFUND_WINDOW_DAYS } from '../src/billing/constants';
import { requestRefund } from '../src/billing/handlers/requestRefund';
import { daysAgo, makeCtx } from './helpers';

// Billing policy BP-12 (March 2026): a customer may ask for a refund up to
// 10 days after a charge. These tests pin that policy.
describe('requestRefund', () => {
  it('refund window is 10 days (billing policy BP-12)', () => {
    expect(REFUND_WINDOW_DAYS).toBe(10);
  });

  it('accepts a request made 9 days after the charge', async () => {
    const ctx = makeCtx({ charges: [{ id: 'ch_1', createdAt: daysAgo(9) }] });
    const res = await requestRefund(ctx, { chargeId: 'ch_1' });
    expect(res.status).toBe('refund_requested');
    expect(ctx.events.map((e) => e.name)).toEqual(['charge.refund_requested']);
  });

  it('rejects a request made 11 days after the charge with REFUND_WINDOW_EXPIRED', async () => {
    const ctx = makeCtx({ charges: [{ id: 'ch_1', createdAt: daysAgo(11) }] });
    await expect(requestRefund(ctx, { chargeId: 'ch_1' })).rejects.toMatchObject({
      code: 'REFUND_WINDOW_EXPIRED',
    });
  });

  it('rejects a second request for the same charge', async () => {
    const ctx = makeCtx({ charges: [{ id: 'ch_1', createdAt: daysAgo(1) }] });
    await requestRefund(ctx, { chargeId: 'ch_1', reason: 'duplicate charge' });
    await expect(requestRefund(ctx, { chargeId: 'ch_1' })).rejects.toMatchObject({
      code: 'REFUND_ALREADY_REQUESTED',
    });
  });

  it('rejects members with FORBIDDEN', async () => {
    const ctx = makeCtx({ role: 'member', charges: [{ id: 'ch_1' }] });
    await expect(requestRefund(ctx, { chargeId: 'ch_1' })).rejects.toMatchObject({ code: 'FORBIDDEN' });
  });
});
