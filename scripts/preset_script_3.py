import os
import re
import sys

# Accept both legacy URL bases
OLD_URL_RE = re.compile(
    r"\((https://pvme(?:\.github)?\.io/preset-maker/#/([A-Za-z0-9]+))\)"
)

def convert_old_url_to_new(preset_id):
    return f"https://presets.pvme.io/?id={preset_id}"

# New header matcher
HEADER_RE = re.compile(
    r"(?i)^#{1,6}[^\n]*p\s*r\s*e\s*s\s*e\s*t[^\n]*$"
)

def process_preset_block(header_line, lines):
    """
    Rewrite a Presets and Relics block:
    - Keep header + tag
    - Delete JSON embed block
    - Rewrite bullets with new URLs
    - Only last bullet gets exposed URL (others wrapped in <>)
    """

    out = [header_line]

    i = 1
    # Keep tag if present
    if i < len(lines) and lines[i].strip().startswith(".tag:presets"):
        out.append(lines[i])
        i += 1

    # Skip blank or '.' lines before JSON
    while i < len(lines) and lines[i].strip() in ("", "."):
        i += 1

    # Capture JSON block until .embed:json
    json_start = i
    while i < len(lines) and ".embed:json" not in lines[i]:
        i += 1
    json_end = i

    json_text = "".join(lines[json_start:json_end])

    # Extract "value":" ... "
    match = re.search(r'"value":"(.*?)"', json_text, flags=re.DOTALL)
    if not match:
        return lines  # fallback – should not happen

    raw = match.group(1)
    bullets = raw.split("\\n")

    # Fix escaped quotes
    bullets = [b.replace('\\"', '"') for b in bullets]

    rewritten = []
    for b in bullets:
        m = OLD_URL_RE.search(b)
        if not m:
            rewritten.append(b)
            continue

        preset_id = m.group(2)
        new_url = convert_old_url_to_new(preset_id)

        rewritten.append((b, new_url))

    # Only last bullet gets live URL, others get <URL>
    final = []
    for idx, item in enumerate(rewritten):
        if isinstance(item, tuple):
            b, new_url = item

            # Prevent double < <url> >
            if new_url.startswith("<") and new_url.endswith(">"):
                clean_url = new_url[1:-1]
            else:
                clean_url = new_url

            if idx < len(rewritten) - 1:
                clean_url = f"<{clean_url}>"

            # Substitute into bullet
            b = OLD_URL_RE.sub(f"({clean_url})", b)
            final.append(b)
        else:
            final.append(item)

    # Output new bullet block
    out.append("\n")
    for line in final:
        out.append(line.rstrip() + "\n")
    out.append("\n")

    return out


def rewrite_file(path):
    with open(path, "r", encoding="utf8") as f:
        lines = f.readlines()

    i = 0
    new_lines = []
    changed = False

    while i < len(lines):
        line = lines[i]

        h = HEADER_RE.match(line)
        if h:
            header_start = i
            header_line = lines[i]
            i += 1

            # Collect lines until .embed:json
            block = [header_line]

            while i < len(lines) and ".embed:json" not in lines[i]:
                block.append(lines[i])
                i += 1

            if i < len(lines) and ".embed:json" in lines[i]:
                block.append(lines[i])
                i += 1

                # Rewrite this block
                rewritten = process_preset_block(header_line, block)
                new_lines.extend(rewritten)
                changed = True
                continue

            # If .embed:json never found, fallback
            new_lines.extend(block)
            continue

        # Otherwise normal line
        new_lines.append(line)
        i += 1

    if changed:
        with open(path, "w", encoding="utf8") as f:
            f.writelines(new_lines)
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
