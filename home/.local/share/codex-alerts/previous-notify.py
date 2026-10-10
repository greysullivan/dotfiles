#!/usr/bin/env python3
"""Send attention-worthy Codex events to the desktop notification daemon."""

import json
import os
import subprocess
import sys


def main() -> int:
    try:
        payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    event = payload.get("type") or payload.get("hook_event_name")
    if event == "agent-turn-complete":
        summary, urgency = "Codex — Done", "normal"
    elif event == "PermissionRequest":
        summary, urgency = "Codex — Approval needed", "critical"
    else:
        return 0

    cwd = payload.get("cwd")
    project = os.path.basename(os.path.normpath(cwd)) if cwd else ""
    command = ["/usr/bin/notify-send", "--app-name=Codex", f"--urgency={urgency}", summary]
    if project:
        command.append(project)
    subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
