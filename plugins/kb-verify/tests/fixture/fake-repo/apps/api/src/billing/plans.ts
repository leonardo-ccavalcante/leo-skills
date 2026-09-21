export const PLAN_IDS = ['starter', 'team', 'business'] as const;

export type PlanId = (typeof PLAN_IDS)[number];

/** Maximum number of members (seats) each plan allows. */
export const PLAN_SEAT_LIMITS: Record<PlanId, number> = {
  starter: 3,
  team: 15,
  business: 50,
};

export function isPlanId(value: string): value is PlanId {
  return (PLAN_IDS as readonly string[]).includes(value);
}
