#!/usr/bin/env python3
"""List the Copilot models available to you, and resolve a fuzzy name to an id.

Model availability is account- and plan-dependent, and the lineup changes over
time, so this queries the live `models.list` RPC rather than trusting a static
table. Use it in preflight: if the user names a model, resolve it to a concrete
id here, then pass that id to the eval scripts via `--model`.

Usage:
    python list_models.py                     # list available models, grouped
    python list_models.py --resolve "opus 4.8"  # -> claude-opus-4.8  (exit 0)
    python list_models.py --resolve "opus"      # ambiguous -> candidates (exit 2)
    python list_models.py --json                # machine-readable list

Exit codes for --resolve: 0 = resolved (id on stdout); 2 = unresolved
(candidates or full list on stderr, nothing on stdout).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys

from eval_harness import DEFAULT_MODEL

try:
    from copilot import CopilotClient
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "The Copilot SDK is not installed. Run: pip install 'github-copilot-sdk>=1.0.0'\n"
        f"(import error: {exc})"
    )

# Ordered so the newest, most-capable families read first in listings.
_VENDORS = [
    ("Anthropic (Claude)", lambda i: i.startswith("claude")),
    ("OpenAI (GPT)", lambda i: i.startswith(("gpt", "o1", "o3", "o4"))),
    ("Google (Gemini)", lambda i: i.startswith("gemini")),
    ("Microsoft", lambda i: i.startswith("mai")),
    ("Other", lambda i: True),
]


async def fetch_models() -> list[dict]:
    """Return [{"id", "name"}] from the live RPC.

    Goes through the raw request rather than the typed `client.list_models()`,
    which raises on models whose billing block omits `multiplier`.
    """
    async with CopilotClient(use_logged_in_user=True) as client:
        resp = await client._client.request("models.list", {})
    out = []
    for m in resp.get("models", []):
        mid = m.get("id")
        if mid:
            out.append({"id": mid, "name": m.get("name") or mid})
    return out


def _norm(s: str) -> str:
    return re.sub(r"[\s_]+", "-", s.strip().lower())


def resolve(query: str, models: list[dict]) -> tuple[str | None, list[str]]:
    """Map a fuzzy model phrase to one id.

    Returns (resolved_id, candidates). If exactly one match, resolved_id is set.
    If zero or several, resolved_id is None and candidates lists what matched
    (empty when nothing matched) — the caller then shows a menu.
    """
    ids = [m["id"] for m in models]
    id_set = set(ids)
    q = query.strip().lower()
    qn = _norm(query)

    if q in id_set:
        return q, [q]
    if qn in id_set:
        return qn, [qn]
    for m in models:                       # exact display-name match
        if m["name"].strip().lower() == q:
            return m["id"], [m["id"]]

    # Token-subset: every token of the query must appear in the id+name.
    tokens = [t for t in re.split(r"[\s\-_]+", q) if t]
    cands: list[str] = []
    for m in models:
        hay = _norm(f"{m['id']} {m['name']}")
        if tokens and all(t in hay for t in tokens):
            cands.append(m["id"])
    seen: set[str] = set()
    cands = [c for c in cands if not (c in seen or seen.add(c))]
    cands.sort(reverse=True)  # newest-first, matching the listing order

    return (cands[0], cands) if len(cands) == 1 else (None, cands)


def group(models: list[dict]) -> list[tuple[str, list[dict]]]:
    """Bucket models by vendor for display, newest-first within a bucket."""
    remaining = list(models)
    grouped = []
    for label, match in _VENDORS:
        bucket = [m for m in remaining if match(m["id"])]
        if bucket:
            bucket.sort(key=lambda m: m["id"], reverse=True)
            grouped.append((label, bucket))
            remaining = [m for m in remaining if m not in bucket]
    return grouped


def format_list(models: list[dict]) -> str:
    lines = []
    for label, bucket in group(models):
        lines.append(f"\n{label}:")
        for m in bucket:
            mark = "  <- default" if m["id"] == DEFAULT_MODEL else ""
            lines.append(f"  {m['id']:<26} {m['name']}{mark}")
    return "\n".join(lines)


async def _amain() -> int:
    ap = argparse.ArgumentParser(description="List or resolve Copilot models")
    ap.add_argument("--resolve", metavar="NAME", help="Resolve a fuzzy model name to an id")
    ap.add_argument("--json", action="store_true", help="Print the raw list as JSON")
    args = ap.parse_args()

    models = await fetch_models()
    if not models:
        print("No models returned. Check that the Copilot CLI is installed and you are signed in.",
              file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(models, indent=2))
        return 0

    if args.resolve:
        resolved, cands = resolve(args.resolve, models)
        if resolved:
            print(resolved)          # the one thing on stdout, for scripting
            return 0
        if cands:
            print(f"'{args.resolve}' is ambiguous. Candidates:", file=sys.stderr)
            for c in cands:
                print(f"  {c}", file=sys.stderr)
        else:
            print(f"'{args.resolve}' matched no available model. Available models:",
                  file=sys.stderr)
            print(format_list(models), file=sys.stderr)
        return 2

    print(f"Models available to this account ({len(models)}):")
    print(format_list(models))
    print(f"\nDefault when unspecified: {DEFAULT_MODEL}")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()
