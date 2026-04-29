"""Entry point for the python-small determinism fixture."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import parser as token_parser  # stdlib 'parser' removed in 3.13; use path insert above


def main():
    tokens = ["a", "b", "c", "d"]
    parsed = token_parser.parse_tokens(tokens)
    unique = token_parser.count_unique(parsed)
    print(f"parsed {unique} unique tokens")


if __name__ == "__main__":
    main()
