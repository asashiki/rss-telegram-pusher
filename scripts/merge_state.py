import json
import sys
from pathlib import Path


def load_json(path, default):
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
        return json.loads(text) if text else default
    except FileNotFoundError:
        return default


def save_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_sent_posts(remote_path, local_path, output_path, max_items=5000):
    merged = []
    seen = set()
    for source_path in (remote_path, local_path):
        for item in load_json(source_path, []):
            key = str(item)
            if key in seen:
                continue
            seen.add(key)
            merged.append(key)
    if max_items > 0:
        merged = merged[-max_items:]
    save_json(output_path, merged)


def merge_rss_state(remote_path, local_path, output_path):
    remote = load_json(remote_path, {})
    local = load_json(local_path, {})
    merged = dict(remote)
    for feed_name, local_state in local.items():
        remote_state = merged.get(feed_name, {})
        if not isinstance(remote_state, dict):
            remote_state = {}
        if not isinstance(local_state, dict):
            merged[feed_name] = local_state
            continue
        next_state = dict(remote_state)
        for key, value in local_state.items():
            if key == "last_checked_at":
                try:
                    value = max(int(value or 0), int(remote_state.get(key) or 0))
                except (TypeError, ValueError):
                    pass
            next_state[key] = value
        merged[feed_name] = next_state
    save_json(output_path, merged)


def main():
    if len(sys.argv) != 6:
        raise SystemExit(
            "usage: merge_state.py REMOTE_SENT LOCAL_SENT OUT_SENT REMOTE_STATE LOCAL_STATE"
        )
    remote_sent, local_sent, out_sent, remote_state, local_state = sys.argv[1:]
    merge_sent_posts(remote_sent, local_sent, out_sent)
    merge_rss_state(remote_state, local_state, "rss_state.json")


if __name__ == "__main__":
    main()
