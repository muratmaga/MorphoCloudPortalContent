# MorphoCloudPortalContent

Runtime content store for MorphoCloud's user-facing emails and pages. The
JSON templates here are **fetched at send/render time** by their consumers,
so edits go live on the next send — no redeploy, no re-vendorize.

**This repo must stay public**: consumers fetch it unauthenticated over
`raw.githubusercontent.com`, which does not serve private repos.

| Template | Consumer | Goes live |
|---|---|---|
| `templates/intake.json` | `morphocloud-intake` (join app: verification email, pages) | next request (5-min cache) |
| `templates/mc-course-intake.json` | `mc-course-intake.gs` (instructor/admin/student emails) | next send (5-min cache) |
| `templates/renewal.json` | `send-renewal-email.yml` (renewal warning + final notice) | next cron send |
| `templates/instance-credentials.json` | `send-email` composite action (individual credential email) | next `/create` or `/email` |

## Editing

Bodies are markdown or HTML (see each file's `_comment`); `{{placeholders}}`
are substituted by the consumer. Validation runs on every push and as a
pre-commit hook (`python3 validate_templates.py`): JSON parse, required
keys per consumer, and `{{placeholder}}` well-formedness. Removing or
renaming a required key breaks the consumer at runtime — the validator's
key lists mirror exactly what each consumer reads.
