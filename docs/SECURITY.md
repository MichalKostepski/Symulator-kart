# Security and usage limitations

## Network scope

This repository is an educational, LAN-only desktop card-game prototype. The host listens on TCP port **5050**, typically on all available local interfaces (`0.0.0.0`).

The current protocol uses unencrypted, unauthenticated JSON over TCP with a 64-byte length header. It does not provide account authentication, access control, TLS, anti-cheat guarantees or hardened handling of malicious client messages.

**Do not expose port 5050 to the internet, forward it through a router or operate the server on an untrusted network.** Use it only with known participants on a private network.

## Local files

The client writes match history and win/loss statistics to `data/`. These plain-text files are intentionally ignored by Git in this portfolio version. Do not commit personal gameplay logs or chat transcripts.

## Dependencies and assets

The game uses only the Python standard library. Original course documents, diagrams and card images are retained for review. Their separate rights and provenance were not independently verified; this repository does not provide a blanket license to reuse these materials.

## Reporting issues

Please open a GitHub issue for non-sensitive functional bugs. Do not post credentials, private addresses, identifiable chat transcripts or exploit details in public issue reports. For sensitive reports, contact a repository maintainer privately.
