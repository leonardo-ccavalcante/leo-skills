import React, { useState } from 'react';
import { t } from '../../i18n';
import type { Session } from '../../types';

// Settings -> Billing -> Invoices tab.
// Offers a range picker and streams the CSV from the API; the API clamps the
// range to its own maximum (apps/api/src/billing/handlers/exportInvoices.ts).
const RANGE_OPTIONS_MONTHS = [3, 6, 12, 24];

export function InvoiceExport({ session }: { session: Session }) {
  const [months, setMonths] = useState(6);
  const [toast, setToast] = useState<string | null>(null);

  function download() {
    window.location.assign(`/api/billing/invoices/export?months=${months}`);
    setToast(t('billing.invoices.ok'));
  }

  return (
    <div>
      <label>
        {t('billing.invoices.range_label')}
        <select value={months} onChange={(e) => setMonths(Number(e.target.value))}>
          {RANGE_OPTIONS_MONTHS.map((m) => (
            <option key={m} value={m}>
              {t('billing.invoices.range_months', { months: m })}
            </option>
          ))}
        </select>
      </label>
      <button onClick={download}>{t('billing.invoices.download')}</button>
      {session.invoiceCount === 0 && <p>{t('billing.invoices.empty')}</p>}
      {toast && <p role="status">{toast}</p>}
    </div>
  );
}
