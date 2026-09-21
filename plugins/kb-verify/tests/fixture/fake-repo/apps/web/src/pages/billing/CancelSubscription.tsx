import React, { useState } from 'react';
import { t } from '../../i18n';
import type { Session } from '../../types';

// Settings -> Billing -> Subscription tab.
// The cancellation is scheduled for the end of the current period; the API
// (apps/api/src/billing/handlers/cancelSubscription.ts) repeats the role
// check, so the disabled button is a courtesy, not the guard.
export function CancelSubscription({ session }: { session: Session }) {
  const [open, setOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const canCancel = session.role === 'owner' || session.role === 'admin';

  async function confirm() {
    const res = await fetch(`/api/billing/subscriptions/${session.subscription.id}/cancel`, {
      method: 'POST',
    });
    const body = await res.json();
    setOpen(false);
    setToast(res.ok ? t('billing.cancel.ok') : t(`billing.errors.${body.code}`));
  }

  return (
    <div>
      <button
        disabled={!canCancel}
        title={canCancel ? undefined : t('billing.cancel.forbidden_hint')}
        onClick={() => setOpen(true)}
      >
        {t('billing.cancel.button')}
      </button>
      {open && (
        <dialog open>
          <h2>{t('billing.cancel.title')}</h2>
          <p>{t('billing.cancel.body')}</p>
          <button onClick={confirm}>{t('billing.cancel.confirm')}</button>
          <button onClick={() => setOpen(false)}>{t('billing.cancel.keep')}</button>
        </dialog>
      )}
      {toast && <p role="status">{toast}</p>}
    </div>
  );
}
