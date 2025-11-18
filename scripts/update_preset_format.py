# Used for the bulk updating of preset embeds to be bulleted normal text instead, with new embedding image preset links
import os
import re
import sys

OLD_URL_RE = re.compile(
    r"https://(?:pvme\.github\.io|pvme\.io)/preset-maker/#/([A-Za-z0-9]+)"
)

def extract_bullets_from_json_block(json_text):
    # Find `"value":" ... "`
    m = re.search(r'"value"\s*:\s*"(.+?)"', json_text, flags=re.DOTALL)
    if not m:
        return None

    block = m.group(1)

    # Split on literal \n inside JSON
    bullets = block.split("\\n")

    cleaned = [b.replace('\\"', '"') for b in bullets]
    return cleaned


def rewrite_bullets(bullets):
    rewritten = []
    id_list = []

    # First pass: convert URLs
    for b in bullets:
        m = OLD_URL_RE.search(b)
        if m:
            preset_id = m.group(1)
            new_url = f"https://presets.pvme.io/?id={preset_id}"
            id_list.append(new_url)
            rewritten.append((b, new_url))
        else:
            rewritten.append(b)

    # Second pass: angle-bracket all except last
    final = []
    for idx, item in enumerate(rewritten):
        if isinstance(item, tuple):
            old_text, new_url = item
            if idx < len(rewritten) - 1:
                # Only wrap if it's not already wrapped
                if not new_url.startswith("<") and not new_url.endswith(">"):
                    new_url = f"<{new_url}>"
            # substitute into bullet
            new_text = OLD_URL_RE.sub(new_url, old_text)
            final.append(new_text)
        else:
            final.append(item)

    return final


def process_preset_section(header_line, tag_line, json_block):
    bullets = extract_bullets_from_json_block(json_block)
    if not bullets:
        return None

    rewritten_bullets = rewrite_bullets(bullets)

    out = []
    out.append(header_line)
    if tag_line:
        out.append(tag_line)

    out.append("\n")
    for b in rewritten_bullets:
        if not b.endswith("\n"):
            b += "\n"
        out.append(b)

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

        if line.strip().startswith("## __Presets and Relics__"):
            header = lines[i]
            i += 1

            tag_line = None
            if i < len(lines) and lines[i].strip().startswith(".tag:"):
                tag_line = lines[i]
                i += 1

            # Now collect the JSON block
            json_start = i
            while i < len(lines) and ".embed:json" not in lines[i]:
                i += 1
            json_end = i

            if i >= len(lines):
                # malformed, restore original
                out.append(header)
                if tag_line:
                    out.append(tag_line)
                continue

            # Full block content
            json_text = "".join(lines[json_start:json_end])

            # Skip the .embed:json line
            i += 1

            rewritten = process_preset_section(header, tag_line, json_text)
            if rewritten:
                out.extend(rewritten)
                changed = True
            else:
                # fallback to original
                out.append(header)
                if tag_line:
                    out.append(tag_line)
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
        print("Usage: python update_presets.py <directory>")
        sys.exit(1)

    walk_directory(sys.argv[1])
