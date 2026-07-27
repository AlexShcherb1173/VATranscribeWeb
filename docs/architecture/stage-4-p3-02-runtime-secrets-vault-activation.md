# Stage 4 / P3-02 Runtime secrets / vault activation

P3-02 converts the P2 secret foundation into an activation workflow.

## Decision

Initial production strategy: `runtime-env-file`.

Runtime file:

```text
/opt/vatranscribe/secrets/.env.runtime
```

Deploy root:

```text
/opt/vatranscribe/app
```

GitHub Environment:

```text
production
```

## Added controls

- Manual runtime env template generator.
- Live runtime env validator wrapper.
- Redacted runtime env evidence generator.
- GitHub Environment secrets checklist.
- Runtime secrets activation checklist.
- Evidence template for release audit.
- Static test coverage for P3-02.

## Production closure

P3-02 is not fully production-closed until the production host has a real runtime env file and the redacted evidence shows that validation passed with no placeholders.

## Secret handling notice

DO NOT commit real secrets, runtime .env.runtime files, private keys, tokens, certificates, backup keys, payment keys, webhook secrets, SMTP passwords, Sentry DSNs, or redacted evidence files to the repository.
