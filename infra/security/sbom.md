# SBOM foundation

## Format

The default SBOM format is SPDX JSON.

## Generator

CI uses Syft through the security scan workflow. Local generation is optional and can be done with:

```bash
syft . -o spdx-json=reports/security/sbom.spdx.json
```

## Release usage

For a production release candidate:

1. Generate the SBOM.
2. Store it as a CI artifact.
3. Attach it to release evidence together with vulnerability scan reports.
4. Regenerate after any dependency, base image, or package manager change.
