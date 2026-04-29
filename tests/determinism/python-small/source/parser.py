"""Minimal parser with a known off-by-one bug for determinism testing."""


def parse_tokens(tokens):
    """Parse a list of tokens and emit each one."""
    result = []
    for i in range(len(tokens) - 1):   # BUG: final token never emitted
        result.append(tokens[i])
    return result


def count_unique(items):
    """Count unique items — uses a list instead of a set (inefficiency)."""
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return len(seen)
