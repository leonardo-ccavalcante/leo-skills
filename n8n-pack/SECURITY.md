# Security policy — n8n skills pack

## Reporting a vulnerability

If you find a security issue in this pack — malicious or unsafe content in a skill file, a bug in the backup-guard hook, guidance that would lead an adopter into an insecure configuration — please report it privately:

- Open a [GitHub private security advisory](https://github.com/leonardo-ccavalcante/leo-skills/security/advisories/new) on this repository, or
- Email the maintainer (address on the GitHub profile) with subject `[leo-skills security]`.

Please include the affected file, the risky guidance or code, and the scenario in which it causes harm. You can expect an acknowledgement within a week. Please do not open public issues for security reports before a fix ships.

## Scope notes

- These skills instruct AI coding agents that hold n8n API credentials. Treat any skill content that would cause an agent to expose credentials, mutate production without a backup, or widen an attack surface as in-scope.
- Operational hardening guidance for adopters lives in [`HARDENING.md`](./HARDENING.md) — that document is guidance, not a warranty.
- Issues in n8n itself belong to [n8n's security process](https://github.com/n8n-io/n8n/blob/master/SECURITY.md), not this repo.
