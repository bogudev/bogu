# Security Policy

## Supported versions

Bogu is pre-1.0 software. Security fixes are provided for the latest published
minor release only.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting feature in the repository Security tab. If that feature
is unavailable, contact the maintainer privately through the contact method
listed on the maintainer's GitHub profile.

Include the affected version, impact, reproduction steps, and any suggested
mitigation. Do not include real personal data or active credentials.

## Security boundaries

- Detection is best-effort and is not a compliance guarantee.
- Reversible placeholders remain personal data when a restoration map exists.
- Session exports contain plaintext private values and require caller-managed
  encryption and access control.
- Previewing and protection are local operations; transmission happens only
  through an explicitly invoked client or application integration.
- Optional detectors and processors have their own dependency and model risks.
