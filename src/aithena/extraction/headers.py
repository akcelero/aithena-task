LINE_PREFIXES = ("#", "//")
BLOCK_DELIMITERS = (('"""', '"""'), ("'''", "'''"), ("/*", "*/"))


def extract_header_comment(text: str) -> str:
    """Return the leading comment block of a file (line/block comments, blank lines included)."""

    lines = text.splitlines()
    result: list[str] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped or stripped.startswith(LINE_PREFIXES):
            result.append(lines[i])
            i += 1
            continue

        opener = next((p for p in BLOCK_DELIMITERS if stripped.startswith(p[0])), None)

        if opener is None:
            break

        start, end = opener
        result.append(lines[i])
        i += 1

        if end in stripped[len(start):]:
            continue

        while i < len(lines):
            result.append(lines[i])
            i += 1

            if end in lines[i - 1]:
                break

    while result and not result[-1].strip():
        result.pop()

    return "\n".join(result)
