import React, { useState } from 'react';
import { t } from '../../i18n';
import type { PlanId, Session } from '../../types';

const PLAN_IDS: PlanId[] = ['starter', 'team', 'business'];

// Settings -> Billing -> Subscription tab.
// The picker only chooses the plan; effective date, proration and the seat
// check live in apps/api/src/billing/handlers/changePlan.ts.
export function ChangePlan({ session }: { session: Session }) {
  const [open, setOpen] = useState(false);
  const [planId, setPlanId] = useState<PlanId>(session.subscription.planId);
  const [toast, setToast] = useState<string | null>(null);

  async function confirm() {
    const res = await fetch(`/api/billing/subscriptions/${session.subscription.id}/plan`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ planId }),
    });
    const body = await res.json();
    setOpen(false);
    setToast(res.ok ? t('billing.plan.ok') : t(`billing.errors.${body.code}`));
  }

  return (
    <div>
      <p>{t('billing.plan.current', { plan: t(`billing.plan.names.${session.subscription.planId}`) })}</p>
      <p>{t('billing.plan.seats', { used: session.seatsInUse, limit: session.subscription.seatLimit })}</p>
      <button onClick={() => setOpen(true)}>{t('billing.plan.change')}</button>
      {open && (
        <dialog open>
          {PLAN_IDS.map((id) => (
            <label key={id}>
              <input type="radio" name="plan" checked={planId === id} onChange={() => setPlanId(id)} />
              {t(`billing.plan.names.${id}`)}
            </label>
          ))}
          <p>{t('billing.plan.prorated')}</p>
          <button onClick={confirm}>{t('billing.plan.confirm')}</button>
          <button onClick={() => setOpen(false)}>{t('common.back')}</button>
        </dialog>
      )}
      {toast && <p role="status">{toast}</p>}
    </div>
  );
}
