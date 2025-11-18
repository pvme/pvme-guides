import os
import re
import sys

# Regex to capture both old URL formats
OLD_URL_RE = re.compile(
    r"https://(?:pvme\.github\.io|pvme\.io)/preset-maker/#/([A-Za-z0-9]+)"
)

def extract_bullets_from_json(json_text):
    m = re.search(r'"value"\s*:\s*"(.+?)"', json_text, flags=re.DOTALL)
    if not m:
        return None
    block = m.group(1)
    bullets = block.split("\\n")
    return [b.replace('\\"', '"') for b in bullets]

def rewrite_bullets(bullets):
    rewritten = []
    for b in bullets:
        m = OLD_URL_RE.search(b)
        if m:
            preset_id = m.group(1)
            new_url = f"https://presets.pvme.io/?id={preset_id}"
            rewritten.append((b, new_url))
        else:
            rewritten.append(b)
    final = []
    for idx, item in enumerate(rewritten):
        if isinstance(item, tuple):
            old_text, new_url = item
            if idx < len(rewritten) - 1 and not new_url.startswith("<") and not new_url.endswith(">"):
                new_url = f"<{new_url}>"
            final.append(OLD_URL_RE.sub(new_url, old_text))
        else:
            final.append(item)
    return final

def process_section(header_line, json_block):
    bullets = extract_bullets_from_json(json_block)
    if not bullets:
        return None
    rewritten = rewrite_bullets(bullets)
    out = [header_line, "\n"]
    for b in rewritten:
        out.append(b + ("\n" if not b.endswith("\n") else ""))
    out.append("\n")
    return out

def rewrite_file(path):
    with open(path, "r", encoding="utf8") as f:
        lines = f.readlines()
    out = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("### Preset and Relics"):
            header = lines[i]
            i += 1
            # Capture JSON block
            json_start = i
            while i < len(lines) and ".embed:json" not in lines[i]:
                i += 1
            json_end = i
            if i < len(lines):
                i += 1  # skip the .embed:json line
            json_text = "".join(lines[json_start:json_end])
            rewritten = process_section(header, json_text)
            if rewritten:
                out.extend(rewritten)
                changed = True
            else:
                out.append(header)
                out.extend(lines[json_start:json_end+1])
        else:
            out.append(line)
            i += 1
    if changed:
        with open(path, "w", encoding="utf8") as f:
            f.writelines(out)
        print(f"Updated: {path}")

def walk_directory(root):
    for subdir, _, files in os.walk(root):
        for file in files:
            if file.lower().endswith(".txt"):
                rewrite_file(os.path.join(subdir, file))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rewrite_presets_alt.py <directory>")
        sys.exit(1)
    walk_directory(sys.argv[1])
