import { describe, expect, it } from 'vitest';
import { cancelSubscription } from '../src/billing/handlers/cancelSubscription';
import { daysFromNow, makeCtx } from './helpers';

describe('cancelSubscription', () => {
  it('schedules the cancellation for the end of the current period', async () => {
    const ctx = makeCtx({ subscriptions: [{ id: 'sub_1', currentPeriodEnd: daysFromNow(20) }] });
    const res = await cancelSubscription(ctx, { subscriptionId: 'sub_1' });
    expect(res.status).toBe('cancel_scheduled');
    expect(res.accessUntil).toEqual(daysFromNow(20));
    const sub = await ctx.db.subscriptions.findById('sub_1');
    expect(sub?.cancelAtPeriodEnd).toBe(true);
    expect(sub?.status).toBe('active');
  });

  it('does not refund anything when cancelling', async () => {
    const ctx = makeCtx({ subscriptions: [{ id: 'sub_1' }] });
    await cancelSubscription(ctx, { subscriptionId: 'sub_1' });
    expect(ctx.events.map((e) => e.name)).toEqual(['subscription.cancel_scheduled']);
  });

  it('rejects a second cancellation with SUB_ALREADY_CANCELLED', async () => {
    const ctx = makeCtx({ subscriptions: [{ id: 'sub_1' }] });
    await cancelSubscription(ctx, { subscriptionId: 'sub_1' });
    await expect(cancelSubscription(ctx, { subscriptionId: 'sub_1' })).rejects.toMatchObject({
      code: 'SUB_ALREADY_CANCELLED',
    });
  });

  it('rejects members with FORBIDDEN', async () => {
    const ctx = makeCtx({ role: 'member', subscriptions: [{ id: 'sub_1' }] });
    await expect(cancelSubscription(ctx, { subscriptionId: 'sub_1' })).rejects.toMatchObject({
      code: 'FORBIDDEN',
    });
  });
});
