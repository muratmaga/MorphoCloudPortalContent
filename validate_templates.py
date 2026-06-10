#!/usr/bin/env python3
"""Validate the runtime email/page templates.

These JSON files are fetched at runtime (raw.githubusercontent.com) by the
join app, the renewal-email workflow, and the course-intake Apps Script —
there is no deploy step, so a malformed file or a renamed key goes live in
minutes and silently breaks production email sending. This script is the
guard rail: it fails if a file doesn't parse, a required key is missing or
empty, or a {{placeholder}} is malformed.

Run directly (python3 validate_templates.py) — used by pre-commit and CI.
"""

import json
import re
import sys
from pathlib import Path

# Keys each consumer reads. Removing or renaming one of these in the JSON
# breaks the consumer at runtime, so all are required.
REQUIRED_KEYS = {
    "templates/intake.json": [
        # join app (morphocloud-intake: email_client.py, main.py)
        "contact_email",
        "invite_msg_already_member",
        "invite_msg_failure",
        "invite_msg_invited",
        "invite_msg_skipped",
        "invite_team_note_individual",
        "invite_team_note_workshop",
        "no_reply_disclaimer",
        "page_already_verified",
        "page_error_config",
        "page_error_invalid_token",
        "page_error_missing_params",
        "page_success_header",
        "verify_email_body",
        "verify_email_subject",
        "workshop_organizer_confirm_body",
        "workshop_organizer_confirm_subject",
    ],
    "templates/mc-course-intake.json": [
        # mc-course-intake.gs
        "admin_approval_body",
        "admin_approval_subject",
        "admin_invalid_handle_body",
        "admin_invalid_handle_subject",
        "approved_body",
        "approved_member_body",
        "approved_subject",
        "contact_email",
        "course_ready_body",
        "course_ready_subject",
        "received_body",
        "received_subject",
        "rejected_body",
        "rejected_subject",
        "student_enrolled_body",
        "student_enrolled_subject",
        "student_invited_body",
        "student_invited_subject",
    ],
    "templates/renewal.json": [
        # send-renewal-email.yml render step
        "contact_email",
        "final_notice_body",
        "final_notice_subject",
        "renewal_available_body",
        "renewal_available_subject",
    ],
}

# A well-formed placeholder: {{identifier}}. Anything else brace-shaped is a
# typo that would survive substitution and reach users verbatim.
PLACEHOLDER_OK = re.compile(r"\{\{[a-z0-9_]+\}\}")


def check_placeholders(text: str) -> list[str]:
    problems = []
    stripped = PLACEHOLDER_OK.sub("", text)
    for match in re.finditer(r"\{\{[^}]*\}\}|\{\{|\}\}", stripped):
        problems.append(f"malformed placeholder near: {match.group(0)!r}")
    return problems


def main() -> int:
    root = Path(__file__).parent
    errors = []

    for rel, required in REQUIRED_KEYS.items():
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: file missing")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON — {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: top level must be an object")
            continue

        for key in required:
            if key not in data:
                errors.append(f"{rel}: missing required key '{key}'")
            elif not isinstance(data[key], str) or not data[key].strip():
                errors.append(f"{rel}: key '{key}' must be a non-empty string")

        for key, value in data.items():
            if isinstance(value, str):
                for problem in check_placeholders(value):
                    errors.append(f"{rel}: key '{key}': {problem}")

    if errors:
        print("Template validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Template validation OK ({len(REQUIRED_KEYS)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
