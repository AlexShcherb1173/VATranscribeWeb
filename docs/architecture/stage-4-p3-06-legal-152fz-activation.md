# Stage 4 / P3-06 — Legal / 152-ФЗ activation

## Status

VATranscribeWeb production legal activation artifact.

Foundation target: legal activation workflow for production release.

Production target: real operator data, 152-ФЗ / РКН / localization decisions, processors inventory, and final legal review are completed outside Git.

## Context

Earlier Stage 4 work created legal/compliance foundation and production guardrails. P3-06 adds the explicit activation layer needed before public release.

## Added controls

- Operator release checklist.
- 152-ФЗ / РКН / localization decision checklist.
- Processors/subprocessors inventory.
- Privacy / Terms / Cookies final review checklist.
- Legal final review evidence template.
- Release checklist integration.
- Static test for P3-06 legal activation artifacts.

## Engineering boundary

The repository contains templates, checklists, and static gates. It must not contain private operator data or final evidence with personal details.

## Foundation closure criteria

- `infra/legal/*` P3-06 documents exist.
- `docs/legal/*` P3-06 release documents exist.
- `docs/release/p3-production-activation-checklist.md` contains the P3-06 block.
- `tests/privacy/test_legal_152fz_activation_static.py` passes.
- Privacy tests pass.
- Web and marketing builds pass.

## Production closure criteria

- Real operator data is filled locally.
- Human/legal review is complete.
- 152-ФЗ applicability decision is recorded.
- RKN notification decision is recorded.
- Personal data localization decision is recorded.
- Processors inventory is complete.
- Evidence is stored outside Git.

## Secret and personal data handling notice

DO NOT commit completed legal evidence, private operator data, user data, personal identifiers, tokens, runtime secrets, payment keys, or provider account details.

This document is not legal advice.
