export type Role = 'owner' | 'admin' | 'member';

export type PlanId = 'starter' | 'team' | 'business';

export interface ChargeSummary {
  id: string;
  description: string;
  amount: string;
  createdAt: string;
}

/** Session payload loaded by the shell before any billing page renders. */
export interface Session {
  workspaceId: string;
  role: Role;
  seatsInUse: number;
  invoiceCount: number;
  subscription: {
    id: string;
    planId: PlanId;
    seatLimit: number;
    currentPeriodEnd: string;
  };
  charges: ChargeSummary[];
  /** Server-side policy values, so the UI never hard-codes them. */
  policy: {
    refundWindowDays: number;
  };
}
