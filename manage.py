"""SkillSprint local management CLI (plan §9, §10).

Usage:
    python manage.py reset-password <email> <new_password>
    python manage.py reseed
    python manage.py inbox show              # list recent LocalInbox messages
    python manage.py inbox mark-read <id>
    python manage.py ollama-model <model>    # persist model name override
    python manage.py stats                   # DB row counts
"""
from __future__ import annotations

import sys

from app import app
from extensions import db
from models import (User, SkillArea, Topic, JobRole, MiniProject,
                    AssessmentQuestion, Lab, ContentItem, TopicHint,
                    CachedResource, LocalInbox)


def reset_password(email: str, new_password: str) -> int:
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if u is None:
            print(f"[ERR] No user with email {email}")
            return 2
        u.set_password(new_password)
        db.session.commit()
        print(f"[OK] Password reset for {email}")
        return 0


def reseed() -> int:
    with app.app_context():
        import seed
        import seed_exercises
        import seed_offline_labs
        import seed_topic_hints
        seed.main()
        seed_exercises.main()
        seed_offline_labs.main()
        seed_topic_hints.main()
        return 0


def set_ollama_model(model: str) -> int:
    import os
    from pathlib import Path
    with app.app_context():
        override = Path(app.config["BASE_DIR"]) / "instance" / "ollama_model.txt"
        override.parent.mkdir(parents=True, exist_ok=True)
        override.write_text(model, encoding="utf-8")
        # Also patch env file for the next launcher run.
        env = Path(app.config["BASE_DIR"]) / ".env"
        if env.exists():
            content = env.read_text()
            if "OLLAMA_MODEL" not in content:
                env.write_text(content + f"\nOLLAMA_MODEL={model}\n", encoding="utf-8")
            else:
                import re
                env.write_text(
                    re.sub(r'(?m)^\s*OLLAMA_MODEL\s*=.*$',
                            f'OLLAMA_MODEL={model}', content),
                    encoding="utf-8")
        print(f"[OK] OLLAMA_MODEL={model} persisted to instance/ollama_model.txt and .env")
    return 0


def inbox_show() -> int:
    with app.app_context():
        rows = (LocalInbox.query
                .order_by(LocalInbox.created_at.desc())
                .limit(20).all())
        if not rows:
            print("(empty)")
            return 0
        for r in rows:
            mark = " " if not r.is_read else "[read]"
            print(f"[{r.id}] {mark} {r.created_at:%Y-%m-%d %H:%M} | "
                  f"{r.name} <{r.email}> | {r.subject}")
            print("    " + (r.body or "")[:180])
    return 0


def inbox_mark_read(inbox_id: int) -> int:
    with app.app_context():
        row = db.session.get(LocalInbox, inbox_id)
        if row is None:
            print(f"[ERR] No LocalInbox row #{inbox_id}")
            return 2
        row.is_read = True
        db.session.commit()
        print(f"[OK] Marked #{inbox_id} as read")
    return 0


def stats() -> int:
    with app.app_context():
        for name, model in [
            ("User", User), ("SkillArea", SkillArea),
            ("Topic", Topic), ("JobRole", JobRole),
            ("MiniProject", MiniProject), ("AssessmentQuestion", AssessmentQuestion),
            ("Lab", Lab), ("ContentItem", ContentItem),
            ("TopicHint", TopicHint), ("CachedResource", CachedResource),
            ("LocalInbox", LocalInbox),
        ]:
            try:
                print(f"  {name:22s} {model.query.count()}")
            except Exception as e:
                print(f"  {name:22s} (err: {e})")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd, rest = argv[1], argv[2:]
    if cmd == "reset-password":
        if len(rest) != 2:
            print("usage: reset-password <email> <new_password>"); return 1
        return reset_password(rest[0], rest[1])
    if cmd == "reseed":
        return reseed()
    if cmd == "ollama-model":
        if len(rest) != 1:
            print("usage: ollama-model <model>"); return 1
        return set_ollama_model(rest[0])
    if cmd == "inbox":
        if not rest:
            print("usage: inbox (show | mark-read <id>)"); return 1
        sub = rest[0]
        if sub == "show":
            return inbox_show()
        if sub == "mark-read":
            if len(rest) != 2:
                print("usage: inbox mark-read <id>"); return 1
            return inbox_mark_read(int(rest[1]))
        print("unknown inbox subcommand:", sub)
        return 1
    if cmd == "stats":
        return stats()
    print("unknown command:", cmd)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
