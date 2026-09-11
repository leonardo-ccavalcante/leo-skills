import { requireRole } from '../../auth/requireRole';
import type { Ctx, Invoice } from '../../types';

export interface ExportInput {
  months: number;
}

export interface CsvDownload {
  filename: string;
  contentType: 'text/csv';
  body: string;
}

// How far back the invoicing provider keeps documents online.
const MAX_EXPORT_MONTHS = 24;

// GET /billing/invoices/export?months=<n>
//
// Any workspace member may download the invoices issued in the last <n>
// months as CSV. The range is clamped to MAX_EXPORT_MONTHS.
export async function exportInvoices(ctx: Ctx, input: ExportInput): Promise<CsvDownload> {
  requireRole(ctx.user, ['owner', 'admin', 'member']);

  const requested = Number.isFinite(input.months) ? Math.floor(input.months) : 1;
  const months = Math.min(Math.max(1, requested), MAX_EXPORT_MONTHS);

  const since = new Date(ctx.now());
  since.setMonth(since.getMonth() - months);

  const invoices = await ctx.db.invoices.list({ workspaceId: ctx.user.workspaceId, since });

  return {
    filename: `invoices-last-${months}-months.csv`,
    contentType: 'text/csv',
    body: toCsv(invoices),
  };
}

function toCsv(invoices: Invoice[]): string {
  const header = 'number,issued_at,total,status';
  const rows = invoices.map(
    (inv) => `${inv.number},${inv.issuedAt.toISOString()},${(inv.totalCents / 100).toFixed(2)},${inv.status}`,
  );
  return [header, ...rows].join('\n') + '\n';
}
