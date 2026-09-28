import { requireRole } from '../../auth/requireRole';
import { ApiError } from '../../errors';
import type { Ctx } from '../../types';
import { MS_PER_DAY, REFUND_PAYOUT_BUSINESS_DAYS, REFUND_WINDOW_DAYS } from '../constants';

export interface RefundInput {
  chargeId: string;
  reason?: string;
}

export interface RefundResult {
  status: 'refund_requested';
  payoutBusinessDays: number;
}

// POST /billing/charges/:id/refund
//
// Owners and admins may ask for a refund of a charge while it is still inside
// the refund window (REFUND_WINDOW_DAYS). One request per charge; a second
// one answers REFUND_ALREADY_REQUESTED.
export async function requestRefund(ctx: Ctx, input: RefundInput): Promise<RefundResult> {
  requireRole(ctx.user, ['owner', 'admin']);

  const charge = await ctx.db.charges.findById(input.chargeId);
  if (!charge || charge.workspaceId !== ctx.user.workspaceId) {
    throw new ApiError('CHARGE_NOT_FOUND');
  }
  if (charge.refundRequestedAt) {
    throw new ApiError('REFUND_ALREADY_REQUESTED');
  }

  const ageDays = (ctx.now().getTime() - charge.createdAt.getTime()) / MS_PER_DAY;
  if (ageDays > REFUND_WINDOW_DAYS) {
    throw new ApiError('REFUND_WINDOW_EXPIRED');
  }

  await ctx.db.charges.update(charge.id, {
    refundRequestedAt: ctx.now(),
    refundReason: input.reason ?? null,
  });
  await ctx.emit('charge.refund_requested', { chargeId: charge.id });

  return { status: 'refund_requested', payoutBusinessDays: REFUND_PAYOUT_BUSINESS_DAYS };
}
