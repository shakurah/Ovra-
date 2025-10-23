"""
Extract JSON-like blocks from a PDF and write them to backend/apps/agent/config/.
Improved heuristics: handles {a, b, c} -> ["a","b","c"], single-id blocks {id} -> {"id": "id"},
and attempts more aggressive quoting for unquoted keys/values.
"""
import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

PDF_PATH = Path("/home/shakz/Downloads/THE ADVANCED LEGAL REASONING CYCLE IN COGNITIVE SYSTEMS.pdf")
OUT_DIR = Path("backend/apps/agent/config")
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_DIR = OUT_DIR / "raw_blocks"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def extract_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    reader = PdfReader(str(pdf_path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n".join(pages)

def find_json_blocks(text: str):
    start = None
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield text[start : i + 1]
                    start = None

def remove_trailing_commas(s: str) -> str:
    return re.sub(r",\s*(?=[}\]])", "", s)

def quote_unquoted_keys(s: str) -> str:
    return re.sub(r'([{\s,])([A-Za-z0-9_@\-]+)\s*:', r'\1"\2":', s)

def quote_unquoted_values(s: str) -> str:
    # add quotes around simple bareword values after colon (best-effort)
    return re.sub(r':\s*([A-Za-z0-9_\-@/]+)(\s*[,\}])', r': "\1"\2', s)

def convert_brace_list_to_array(s: str):
    # {a, b, c} -> ["a","b","c"]
    inner = s.strip()[1:-1]
    parts = [p.strip() for p in inner.split(",") if p.strip()]
    # if parts look like key:value items, don't convert
    if any(":" in p for p in parts):
        return None
    return json.dumps(parts, ensure_ascii=False)

def wrap_single_identifier(s: str):
    # {id} -> {"id": "id"}
    inner = s.strip()[1:-1].strip()
    if inner and re.fullmatch(r"[A-Za-z0-9_\-@]+", inner):
        return json.dumps({inner: inner}, ensure_ascii=False)
    return None

def try_parse_and_write(block_text: str, idx: int):
    raw_path = RAW_DIR / f"raw_block_{idx}.txt"
    raw_path.write_text(block_text[:20000], encoding="utf-8")
    print(f"[INFO] wrote raw block to {raw_path} (first 20000 chars)")

    preview = block_text.strip()[:400].replace("\n", "\\n")
    print(f"[PREVIEW #{idx}] {preview}...")

    attempts = []
    attempts.append(("original", block_text))
    attempts.append(("smartquotes", block_text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")))
    attempts.append(("remove_hyphenation", re.sub(r"-\s*\n\s*", "", block_text)))
    attempts.append(("join_lines", block_text.replace("\n", " ")))
    attempts.append(("smart_join", block_text.replace("“", '"').replace("”", '"').replace("\n", " ")))
    attempts.append(("remove_trailing_commas", remove_trailing_commas(block_text)))
    attempts.append(("quote_keys", quote_unquoted_keys(remove_trailing_commas(block_text.replace("\n", " ")))))
    attempts.append(("quote_keys_and_values", quote_unquoted_values(quote_unquoted_keys(remove_trailing_commas(block_text.replace("\n", " "))))))

    # Add more aggressive transformations (list / single-id)
    list_conv = convert_brace_list_to_array(block_text)
    if list_conv:
        attempts.append(("brace_list_to_array", list_conv))
    single_conv = wrap_single_identifier(block_text)
    if single_conv:
        attempts.append(("single_identifier_wrap", single_conv))

    for name, attempt in attempts:
        try:
            obj = json.loads(attempt)
            out_path = OUT_DIR / f"extracted_{idx}.json"
            out_path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[OK] parsed block #{idx} using '{name}' -> wrote {out_path}")
            return True
        except Exception as e:
            print(f"[DEBUG] attempt '{name}' failed for block #{idx}: {e}")

    print(f"[WARN] block #{idx} not valid JSON after attempts (raw saved).")
    return False

def main():
    try:
        text = extract_text(PDF_PATH)
    except FileNotFoundError as e:
        print(str(e))
        return
    count = 0
    for i, block in enumerate(find_json_blocks(text), start=1):
        if try_parse_and_write(block, i):
            count += 1
    print(f"Done. {count} JSON files extracted to {OUT_DIR} (raw blocks in {RAW_DIR})")

if __name__ == "__main__":
    main()