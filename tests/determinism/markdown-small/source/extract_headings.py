import re


def extract_headings(text):
    """Extract (level, title, next_line) tuples from markdown text."""
    lines = text.splitlines()
    headings = []
    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # Off-by-one: crashes with IndexError when the last line is a heading.
            # Condition should be `i + 1 < len(lines)`.
            next_line = lines[i + 1] if i < len(lines) else ""
            headings.append((level, title, next_line))
    return headings


def slug(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
