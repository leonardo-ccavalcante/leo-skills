import type { PlanId } from './billing/plans';

export type Role = 'owner' | 'admin' | 'member';

export interface User {
  id: string;
  workspaceId: string;
  role: Role;
}

export interface Subscription {
  id: string;
  workspaceId: string;
  planId: PlanId;
  status: 'active' | 'cancelled';
  cancelAtPeriodEnd: boolean;
  currentPeriodEnd: Date;
  cancelledAt: Date | null;
}

export interface Charge {
  id: string;
  workspaceId: string;
  amountCents: number;
  createdAt: Date;
  refundRequestedAt: Date | null;
  refundReason: string | null;
}

export interface Invoice {
  id: string;
  workspaceId: string;
  number: string;
  issuedAt: Date;
  totalCents: number;
  status: 'paid' | 'open' | 'void';
}

export interface Table<T extends { id: string }> {
  findById(id: string): Promise<T | undefined>;
  update(id: string, patch: Partial<T>): Promise<T>;
  list(filter: { workspaceId: string; since?: Date }): Promise<T[]>;
}

export interface Db {
  subscriptions: Table<Subscription>;
  charges: Table<Charge>;
  invoices: Table<Invoice>;
  members: { count(workspaceId: string): Promise<number> };
}

/** Per-request context handed to every handler. */
export interface Ctx {
  db: Db;
  user: User;
  now(): Date;
  emit(event: string, payload: unknown): Promise<void>;
}
