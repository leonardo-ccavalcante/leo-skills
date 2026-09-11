# acme/monorepo

Billing area of the Acme product, split into two packages:

- `apps/web` — React front end. Pages live under `src/pages/billing`; every
  user-facing string is a key in `locales/<locale>.json` resolved by `src/i18n.ts`.
- `apps/api` — HTTP handlers under `src/billing/handlers`, shared constants in
  `src/billing/constants.ts`, plan limits in `src/billing/plans.ts`, the error
  catalog in `src/errors.ts` and tests under `test/`.

Error codes (for example `SUB_ALREADY_CANCELLED`) are shared between the API
and the front end: the API throws the code, the front end shows
`billing.errors.<CODE>` from the active locale.

Run `npm test` at the root to execute every package's tests.
