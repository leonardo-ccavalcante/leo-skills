import React, { useState } from 'react';
import { t } from '../../i18n';
import type { Session } from '../../types';

// Settings -> Billing -> Refunds tab.
// Lists the recent charges; the API decides whether a charge is still inside
// the refund window and answers with an error code otherwise.
export function RequestRefund({ session }: { session: Session }) {
  const [reason, setReason] = useState('');
  const [toast, setToast] = useState<string | null>(null);
  const canRequest = session.role === 'owner' || session.role === 'admin';

  async function request(chargeId: string) {
    const res = await fetch(`/api/billing/charges/${chargeId}/refund`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    const body = await res.json();
    setToast(
      res.ok
        ? t('billing.refund.ok', { days: body.payoutBusinessDays })
        : t(`billing.errors.${body.code}`),
    );
  }

  return (
    <div>
      <p>{t('billing.refund.hint', { days: session.policy.refundWindowDays })}</p>
      <label>
        {t('billing.refund.reason_label')}
        <input value={reason} onChange={(e) => setReason(e.target.value)} />
      </label>
      <ul>
        {session.charges.map((charge) => (
          <li key={charge.id}>
            {charge.description} - {charge.amount} - {charge.createdAt}
            <button disabled={!canRequest} onClick={() => request(charge.id)}>
              {t('billing.refund.button')}
            </button>
          </li>
        ))}
      </ul>
      {toast && <p role="status">{toast}</p>}
    </div>
  );
}
