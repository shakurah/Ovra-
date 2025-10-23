"""
Normalize raw PDF blocks saved by extract_pdf_json.py into valid JSON files
and write them to backend/apps/agent/config/extracted_*.json

Run from repo root:
  python3 scripts/normalize_raw_blocks.py
"""
import re
import json
from pathlib import Path

RAW_DIR = Path("backend/apps/agent/config/raw_blocks")
OUT_DIR = Path("backend/apps/agent/config")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def try_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None

def convert_brace_list(s):
    # {a, b, c} -> ["a","b","c"]
    inner = s.strip()[1:-1]
    parts = [p.strip().strip('"').strip("'") for p in inner.split(",") if p.strip()]
    if parts and all(re.fullmatch(r"[A-Za-z0-9_\-@/\. ]+", p) for p in parts):
        return json.dumps(parts, ensure_ascii=False)
    return None

def wrap_single_id(s):
    inner = s.strip()[1:-1].strip()
    if inner and re.fullmatch(r"[A-Za-z0-9_\-@/\.]+", inner):
        return json.dumps({inner: inner}, ensure_ascii=False)
    return None

def add_quotes_to_keys(s):
    return re.sub(r'([{\s,])([A-Za-z0-9_\-@/\.]+)\s*:', r'\1"\2":', s)

def quote_bare_values(s):
    return re.sub(r':\s*([A-Za-z0-9_\-@/\.]+)(\s*[,\}])', r': "\1"\2', s)

def remove_trailing_commas(s):
    return re.sub(r',\s*(?=[\}\]])', '', s)

def normalize_text(s):
    # conservative normalizations
    s1 = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s1 = re.sub(r'-\s*\n\s*', '', s1)            # remove hyphenation
    s1 = s1.replace('\n', ' ')
    s1 = remove_trailing_commas(s1)
    return s1.strip()

def process_file(p: Path, idx: int):
    raw = p.read_text(encoding="utf-8")
    preview = raw.strip()[:300].replace("\n", "\\n")
    print(f"[INFO] processing {p.name}: {preview}...")
    # try raw load
    if j := try_json(raw):
        (OUT_DIR / f"extracted_{idx}.json").write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] raw JSON parsed -> extracted_{idx}.json")
        return True

    s_norm = normalize_text(raw)

    # attempt list conversion
    if s_norm.startswith("{") and s_norm.endswith("}") and not ":" in s_norm:
        if conv := convert_brace_list(s_norm):
            if j := try_json(conv):
                (OUT_DIR / f"extracted_{idx}.json").write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[OK] brace-list -> extracted_{idx}.json")
                return True
        if conv := wrap_single_id(s_norm):
            if j := try_json(conv):
                (OUT_DIR / f"extracted_{idx}.json").write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[OK] single-id -> extracted_{idx}.json")
                return True

    # progressive repair attempts
    attempts = [
        s_norm,
        add_quotes_to_keys(s_norm),
        quote_bare_values(add_quotes_to_keys(s_norm)),
        '{"data": ' + s_norm + '}',  # wrap as a value
    ]
    for attempt in attempts:
        if j := try_json(attempt):
            (OUT_DIR / f"extracted_{idx}.json").write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[OK] parsed using attempt -> extracted_{idx}.json")
            return True

    # failed: write failed sample for manual inspection
    fail_path = OUT_DIR / f"failed_{idx}.txt"
    fail_path.write_text(raw[:20000], encoding="utf-8")
    print(f"[WARN] failed to parse -> wrote {fail_path}")
    return False

def main():
    files = sorted(RAW_DIR.glob("raw_block_*.txt"))
    if not files:
        print("[ERROR] no raw blocks found in", RAW_DIR)
        return
    succeeded = 0
    for i, f in enumerate(files, start=1):
        if process_file(f, i):
            succeeded += 1
    print(f"Done. {succeeded}/{len(files)} blocks converted. Clean files in {OUT_DIR}")

if __name__ == "__main__":
    main()