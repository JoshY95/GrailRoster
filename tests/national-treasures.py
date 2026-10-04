"""Source-backed import regression: stable identities, reruns and conflict refusal."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SET_ID = "2024-panini-national-treasures-wwe"
SOURCE = ROOT / "sources" / SET_ID / "checklist.xls"


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("data", "sql") for p in (root / folder).rglob("*") if p.is_file()}


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "scripts").mkdir()
    for filename in ("catalogue_io.py", "add_2024_panini_national_treasures_wwe.py"):
        shutil.copyfile(ROOT / "scripts" / filename, root / "scripts" / filename)
    (root / "data" / "sets").mkdir(parents=True)
    sentinel = {"id": "existing-card", "setId": "existing-set", "order": 1,
                "name": "Existing collection identity", "number": "1"}
    old_file = root / "data" / "sets" / "existing-set.json"
    old_file.write_text(json.dumps({"setId": "existing-set", "cards": [sentinel]}, separators=(",", ":")))
    original = old_file.read_bytes()
    (root / "data" / "catalogue-index.json").write_text(json.dumps({
        "setCount": 1, "cardCount": 1,
        "sets": [{"id": "existing-set", "name": "Existing set", "cardCount": 1,
                  "releaseDate": "2024-01-01", "file": "sets/existing-set.json"}],
    }))
    command = [sys.executable, str(root / "scripts" / "add_2024_panini_national_treasures_wwe.py"),
               str(SOURCE), "--sql-dir", str(root / "sql")]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    cards = json.loads((root / "data" / "sets" / (SET_ID + ".json")).read_text())["cards"]
    assert len(cards) == len({c["id"] for c in cards}) == 718
    assert len({c["subset"] for c in cards}) == 21
    assert sum(c["subset"] == "Triple Signatures" for c in cards) == 2
    assert sum(c["subset"] == "Dual Signatures" for c in cards) == 11
    assert old_file.read_bytes() == original
    before = hashes(root)
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert hashes(root) == before, "Reimport must not change catalogue or SQL bytes"
    assert old_file.read_bytes() == original

    # A conflicting existing identity must stop the import before rewriting anything.
    target = root / "data" / "sets" / (SET_ID + ".json")
    payload = json.loads(target.read_text())
    payload["cards"][0]["name"] = "Unexpected conflicting identity"
    target.write_text(json.dumps(payload))
    before = hashes(root)
    rejected = subprocess.run(command, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert "differs from the source workbook" in rejected.stderr
    assert hashes(root) == before, "A rejected import must leave all files untouched"

print("PASS: source counts, stable multi-subject identities, existing-file preservation, "
      "byte-identical reimport, and conflict refusal before writes.")
