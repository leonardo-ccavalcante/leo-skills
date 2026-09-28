import React, { useState } from 'react';
import { t } from '../../i18n';
import type { Session } from '../../types';
import { CancelSubscription } from './CancelSubscription';
import { ChangePlan } from './ChangePlan';
import { InvoiceExport } from './InvoiceExport';
import { RequestRefund } from './RequestRefund';

type Tab = 'subscription' | 'invoices' | 'refunds';

const TABS: Tab[] = ['subscription', 'invoices', 'refunds'];

// Route: /settings/billing (sidebar: Settings -> Billing).
export function BillingSettings({ session }: { session: Session }) {
  const [tab, setTab] = useState<Tab>('subscription');

  return (
    <section>
      <nav aria-label="breadcrumb">
        {t('common.settings')} / {t('common.billing')}
      </nav>
      <div role="tablist">
        {TABS.map((key) => (
          <button role="tab" key={key} aria-selected={tab === key} onClick={() => setTab(key)}>
            {t(`billing.tabs.${key}`)}
          </button>
        ))}
      </div>
      {tab === 'subscription' && (
        <>
          <ChangePlan session={session} />
          <CancelSubscription session={session} />
        </>
      )}
      {tab === 'invoices' && <InvoiceExport session={session} />}
      {tab === 'refunds' && <RequestRefund session={session} />}
    </section>
  );
}
