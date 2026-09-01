# Domain Docs

- Layout: **single-context** — one `CONTEXT.md` + `docs/adr/` at repo root.
- `CONTEXT.md` exists (Turkish glossary, `Mazak Izleme`). It grows during
  `/alp-hizala` (grill-with-docs) sessions as terms get resolved — do not
  rewrite it wholesale.
- Architectural decisions go under `docs/adr/` as they are made.

## Before exploring, read these
- `CONTEXT.md` at the repo root.
- The ADRs under `docs/adr/` that touch the area you are about to work in.

## Use the glossary's vocabulary
When your output names a domain concept (issue title, refactor proposal,
hypothesis, test name), use the term as `CONTEXT.md` defines it — Turkish term
first, English identifier as written there (Tezgah/`machine`, Cevrim/`cycle`,
Olay/`event`). Do not drift to synonyms the glossary avoids.

If a concept you need is missing from the glossary, that is a signal: either
you are inventing language the project does not use (reconsider), or there is a
real gap (note it for `/alp-hizala`).

## Flag ADR conflicts
If your output contradicts an existing ADR, say so explicitly instead of
silently overriding it:

> _ADR-0004 (izleme karari kutuya ait, salt okunur) ile celisiyor — ama su
> nedenle yeniden acilmali…_