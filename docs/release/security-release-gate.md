# Security release gate

Before a production release, attach or link the following evidence:

- Full test run result.
- Web and marketing production build result.
- Docker compose production config validation.
- Python dependency audit result.
- Node dependency audit result.
- Trivy filesystem/config/container scan result.
- Gitleaks secret scan result.
- SBOM artifact.
- Vulnerability triage notes for every non-blocking finding.

## Blocking criteria

Production release is blocked by:

- Critical vulnerability.
- High vulnerability.
- Real secret detected in repository history or current tree.
- Missing lockfile or dependency manifest.
- Disabled security scan workflow.
- Missing release owner sign-off.

## Manual review criteria

Medium vulnerabilities require manual review and documented decision before release. Low vulnerabilities can be accepted with review.
