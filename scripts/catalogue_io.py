"""Per-set catalogue storage. Unchanged set files are never rewritten."""
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
INDEX = DATA / "catalogue-index.json"


def load_catalogue():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    cards = []
    for item in index["sets"]:
        payload = json.loads((DATA / item["file"]).read_text(encoding="utf-8"))
        if payload["setId"] != item["id"]:
            raise ValueError("Set file identity mismatch")
        cards.extend(payload["cards"])
    return {**index, "sets": [{k: v for k, v in s.items() if k != "file"} for s in index["sets"]], "cards": cards}


def write_if_changed(path, payload):
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def save_catalogue(catalogue):
    sets, cards = catalogue["sets"], catalogue["cards"]
    ids = {s["id"] for s in sets}
    if len(ids) != len(sets) or len({c["id"] for c in cards}) != len(cards):
        raise ValueError("Duplicate set/card IDs")
    if any(c["setId"] not in ids for c in cards):
        raise ValueError("Orphan catalogue card")
    indexed_sets = []
    for item in sets:
        if not re.fullmatch(r"[a-z0-9-]+", item["id"]):
            raise ValueError("Unsafe set ID")
        subset_cards = [c for c in cards if c["setId"] == item["id"]]
        if len(subset_cards) != item["cardCount"]:
            raise ValueError("Set count mismatch")
        relative = f'sets/{item["id"]}.json'
        write_if_changed(DATA / relative, {"setId": item["id"], "cards": subset_cards})
        indexed_sets.append({**item, "file": relative})
    write_if_changed(INDEX, {**{k: v for k, v in catalogue.items() if k not in ("sets", "cards")},
                             "setCount": len(sets), "cardCount": len(cards), "sets": indexed_sets})


if __name__ == "__main__":
    if sys.argv[1:] == ["--read"]:
        print(json.dumps(load_catalogue(), ensure_ascii=False, separators=(",", ":")))
    elif sys.argv[1:] == ["--write"]:
        save_catalogue(json.load(sys.stdin))
    elif sys.argv[1:] == ["--migrate"]:
        save_catalogue(json.loads((DATA / "catalogue.json").read_text(encoding="utf-8")))
    else:
        raise SystemExit("Usage: catalogue_io.py --read | --write | --migrate")
