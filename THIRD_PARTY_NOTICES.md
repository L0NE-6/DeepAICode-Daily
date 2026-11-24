# Third-Party Notices

This repository contains an independently written Python implementation of the
DeepAI Code daily Theos grant flow. API keys are supplied at runtime and are
not included in the repository.

## Protocol Evidence

### magpie-deepaicode

- Source: `aqiu817/magpie-deepaicode`
- Fixed commit reviewed: `1c9837c2f32a70229799973982bea4b5ba6ca4f9`
- License: MIT
- Use: `/deepai_code/theos` request headers, device fingerprint requirement,
  response fields, and grant-state semantics were reviewed as protocol evidence.
- Local implementation: Python, requests-based, independently structured, with
  a persisted refresh_at baseline and no repeated polling.

## Runtime Dependencies

- `requests` is installed from PyPI under its own license.

## Project License

The local implementation is released under the MIT License reproduced in
[`LICENSE`](LICENSE).
