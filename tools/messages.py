#!/usr/bin/env python3
"""Append-only message channel between the two agents and the user.

Two files under reference/, one writer each, never edited in place:

    reference/messages-from-browser.jsonl
    reference/messages-from-ledger.jsonl

Appending needs no lock and no unlink, which is why this works from the
browser agent's side of the folder where git and SQLite do not. Records are
one JSON object per line:

    {"id": "browser-20260911-1", "ts": "2026-09-11T14:02:11-04:00",
     "from": "browser", "to": "ledger", "type": "request",
     "subject": "...", "body": "...", "refs": ["reference/incoming.tsv"], "re": null}

  to    ledger | browser | user
  type  request  - the recipient must act; open until a reply with type done
        done     - closes the request named in "re"
        question - needs an answer; open until a reply with type answer
        answer   - answers the question named in "re"
        info     - nothing to do; never open

Usage (from the repository root, as the agent you are):

    python3 tools/messages.py send   <me> <to> <type> "<subject>" ["<body>"] [--re ID] [--ref PATH ...]
    python3 tools/messages.py pending <me>          # open items addressed to me
    python3 tools/messages.py list   [N]            # last N messages, both files, by time
    python3 tools/messages.py show   <ID>

Only ever `send` as yourself: the file it writes is chosen by <me>. The user
sends as "user" and may write either file — say which with --via.
"""
import json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "browser": ROOT / "reference" / "messages-from-browser.jsonl",
    "ledger": ROOT / "reference" / "messages-from-ledger.jsonl",
}
PARTIES = ("browser", "ledger", "user")
TYPES = ("request", "done", "question", "answer", "info")
CLOSES = {"done": "request", "answer": "question"}


def load():
    msgs = []
    for who, path in FILES.items():
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"{path.name}:{n}: unreadable line skipped ({exc})", file=sys.stderr)
                continue
            m["_file"] = who
            msgs.append(m)
    msgs.sort(key=lambda m: m.get("ts", ""))
    return msgs


def next_id(sender, msgs):
    today = datetime.date.today().strftime("%Y%m%d")
    prefix = f"{sender}-{today}-"
    n = 1 + sum(1 for m in msgs if str(m.get("id", "")).startswith(prefix))
    return f"{prefix}{n}"


def cmd_send(argv):
    opts = {"re": None, "ref": [], "via": None}
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--re":
            opts["re"] = argv[i + 1]; i += 2
        elif a == "--ref":
            opts["ref"].append(argv[i + 1]); i += 2
        elif a == "--via":
            opts["via"] = argv[i + 1]; i += 2
        else:
            pos.append(a); i += 1
    if len(pos) < 4:
        sys.exit("usage: send <me> <to> <type> <subject> [body] [--re ID] [--ref PATH] [--via browser|ledger]")
    me, to, typ, subject = pos[:4]
    body = pos[4] if len(pos) > 4 else ""
    if me not in PARTIES or to not in PARTIES or typ not in TYPES:
        sys.exit(f"from/to must be one of {PARTIES}, type one of {TYPES}")
    if typ in CLOSES and not opts["re"]:
        sys.exit(f"type {typ} needs --re <id of the {CLOSES[typ]} it closes>")
    via = opts["via"] or me
    if via not in FILES:
        sys.exit("the user must say --via browser or --via ledger")
    msgs = load()
    if opts["re"] and not any(m.get("id") == opts["re"] for m in msgs):
        sys.exit(f"no message with id {opts['re']}")
    rec = {
        "id": next_id(me, msgs),
        "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "from": me, "to": to, "type": typ,
        "subject": subject, "body": body,
        "refs": opts["ref"], "re": opts["re"],
    }
    path = FILES[via]
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(rec["id"])


def open_items(msgs, me=None):
    closed = {m["re"] for m in msgs if m.get("type") in CLOSES and m.get("re")}
    for m in msgs:
        if m.get("type") in ("request", "question") and m.get("id") not in closed:
            if me is None or m.get("to") == me:
                yield m


def fmt(m, full=False):
    head = f"{m.get('id','?'):<22} {m.get('ts','')[:16]}  {m.get('from','?')} -> {m.get('to','?')}  [{m.get('type','?')}]  {m.get('subject','')}"
    if not full:
        return head
    lines = [head]
    if m.get("re"):
        lines.append(f"  re:   {m['re']}")
    for r in m.get("refs") or []:
        lines.append(f"  ref:  {r}")
    if m.get("body"):
        lines.append("")
        lines.extend("  " + l for l in m["body"].splitlines())
    return "\n".join(lines)


def cmd_pending(argv):
    me = argv[0] if argv else None
    if me and me not in PARTIES:
        sys.exit(f"who? one of {PARTIES}")
    items = list(open_items(load(), me))
    if not items:
        print("nothing pending" + (f" for {me}" if me else ""))
        return
    for m in items:
        print(fmt(m, full=True))
        print()


def cmd_list(argv):
    n = int(argv[0]) if argv else 20
    msgs = load()
    closed = {m["re"] for m in msgs if m.get("type") in CLOSES and m.get("re")}
    for m in msgs[-n:]:
        mark = " (closed)" if m.get("id") in closed else ""
        print(fmt(m) + mark)


def cmd_show(argv):
    if not argv:
        sys.exit("usage: show <ID>")
    for m in load():
        if m.get("id") == argv[0]:
            print(fmt(m, full=True))
            return
    sys.exit(f"no message {argv[0]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pending"
    {"send": cmd_send, "pending": cmd_pending, "list": cmd_list, "show": cmd_show}.get(
        cmd, lambda a: sys.exit(__doc__))(sys.argv[2:])
