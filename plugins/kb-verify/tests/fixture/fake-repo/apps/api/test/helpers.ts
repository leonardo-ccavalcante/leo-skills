import type { PlanId } from '../src/billing/plans';
import type { Charge, Ctx, Invoice, Role, Subscription, Table } from '../src/types';

export const NOW = new Date('2026-09-01T12:00:00Z');

export function daysAgo(days: number): Date {
  return new Date(NOW.getTime() - days * 86_400_000);
}

export function daysFromNow(days: number): Date {
  return new Date(NOW.getTime() + days * 86_400_000);
}

function memoryTable<T extends { id: string; workspaceId: string }>(rows: T[]): Table<T> {
  const byId = new Map(rows.map((row) => [row.id, { ...row }]));
  return {
    async findById(id) {
      return byId.get(id);
    },
    async update(id, patch) {
      const next = { ...byId.get(id)!, ...patch };
      byId.set(id, next);
      return next;
    },
    async list(filter) {
      return [...byId.values()].filter((row) => row.workspaceId === filter.workspaceId);
    },
  };
}

export interface Seed {
  role?: Role;
  subscriptions?: Array<Partial<Subscription> & { id: string }>;
  charges?: Array<Partial<Charge> & { id: string }>;
  invoices?: Array<Partial<Invoice> & { id: string }>;
  memberCount?: number;
}

export interface TestCtx extends Ctx {
  events: Array<{ name: string; payload: unknown }>;
}

/** In-memory context for workspace `ws_1`; the acting user is `usr_1`. */
export function makeCtx(seed: Seed = {}): TestCtx {
  const subscriptions: Subscription[] = (seed.subscriptions ?? []).map((s) => ({
    workspaceId: 'ws_1',
    planId: 'team' as PlanId,
    status: 'active',
    cancelAtPeriodEnd: false,
    currentPeriodEnd: daysFromNow(20),
    cancelledAt: null,
    ...s,
  }));
  const charges: Charge[] = (seed.charges ?? []).map((c) => ({
    workspaceId: 'ws_1',
    amountCents: 4900,
    createdAt: NOW,
    refundRequestedAt: null,
    refundReason: null,
    ...c,
  }));
  const invoices: Invoice[] = (seed.invoices ?? []).map((i) => ({
    workspaceId: 'ws_1',
    number: `INV-${i.id}`,
    issuedAt: NOW,
    totalCents: 4900,
    status: 'paid',
    ...i,
  }));
  const events: TestCtx['events'] = [];

  return {
    db: {
      subscriptions: memoryTable(subscriptions),
      charges: memoryTable(charges),
      invoices: memoryTable(invoices),
      members: { count: async () => seed.memberCount ?? 1 },
    },
    user: { id: 'usr_1', workspaceId: 'ws_1', role: seed.role ?? 'owner' },
    now: () => NOW,
    emit: async (name, payload) => {
      events.push({ name, payload });
    },
    events,
  };
}
