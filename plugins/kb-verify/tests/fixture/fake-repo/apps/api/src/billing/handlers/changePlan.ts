import { requireRole } from '../../auth/requireRole';
import { ApiError } from '../../errors';
import type { Ctx } from '../../types';
import { PLAN_SEAT_LIMITS, isPlanId } from '../plans';

export interface ChangePlanInput {
  subscriptionId: string;
  planId: string;
}

export interface ChangePlanResult {
  status: 'plan_changed';
  effective: 'immediately';
  prorated: true;
  seatLimit: number;
}

// POST /billing/subscriptions/:id/plan
//
// Switches the workspace to another plan. The change is effective
// immediately; the payment provider prorates the price difference for the
// rest of the period. A downgrade is refused while the workspace has more
// members than the target plan allows (PLAN_SEAT_LIMIT_EXCEEDED).
export async function changePlan(ctx: Ctx, input: ChangePlanInput): Promise<ChangePlanResult> {
  requireRole(ctx.user, ['owner', 'admin']);

  if (!isPlanId(input.planId)) {
    throw new ApiError('PLAN_UNKNOWN');
  }
  const sub = await ctx.db.subscriptions.findById(input.subscriptionId);
  if (!sub || sub.workspaceId !== ctx.user.workspaceId) {
    throw new ApiError('SUB_NOT_FOUND');
  }

  const seatLimit = PLAN_SEAT_LIMITS[input.planId];
  const seatsInUse = await ctx.db.members.count(ctx.user.workspaceId);
  if (seatsInUse > seatLimit) {
    throw new ApiError('PLAN_SEAT_LIMIT_EXCEEDED');
  }

  await ctx.db.subscriptions.update(sub.id, { planId: input.planId });
  await ctx.emit('subscription.plan_changed', {
    subscriptionId: sub.id,
    from: sub.planId,
    to: input.planId,
    prorate: true,
  });

  return { status: 'plan_changed', effective: 'immediately', prorated: true, seatLimit };
}
