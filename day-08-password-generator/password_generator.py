# Author: Mashhood Ali
"""Secure password generator.

Generates cryptographically strong passwords with the ``secrets`` module
(never ``random``, which is not safe for secrets). Every password is
guaranteed to contain at least one character from each selected character
set, and each one is reported with its estimated entropy in bits so you
can tell at a glance how hard it is to brute-force.

Usage:
    python3 password_generator.py
    python3 password_generator.py --length 20 --count 5
    python3 password_generator.py --length 12 --no-symbols --json
    python3 password_generator.py --length 24 --exclude-ambiguous
"""

import argparse
import json
import math
import secrets
import string
import sys

AMBIGUOUS = "l1IO0"

SETS = {
    "lowercase": string.ascii_lowercase,
    "uppercase": string.ascii_uppercase,
    "digits": string.digits,
    "symbols": string.punctuation,
}


def build_sets(args):
    """Return the enabled character sets, honouring the --no-* flags."""
    enabled = {}
    if not args.no_lowercase:
        enabled["lowercase"] = SETS["lowercase"]
    if not args.no_uppercase:
        enabled["uppercase"] = SETS["uppercase"]
    if not args.no_digits:
        enabled["digits"] = SETS["digits"]
    if not args.no_symbols:
        enabled["symbols"] = SETS["symbols"]
    if args.exclude_ambiguous:
        for name in enabled:
            enabled[name] = "".join(
                ch for ch in enabled[name] if ch not in AMBIGUOUS
            )
    return {name: chars for name, chars in enabled.items() if chars}


def generate_password(length, sets):
    """Build one password with at least one char from each set."""
    pool = "".join(sets.values())
    # One guaranteed character per set, then fill the rest from the pool.
    chars = [secrets.choice(chars) for chars in sets.values()]
    chars += [secrets.choice(pool) for _ in range(length - len(chars))]
    # Shuffle with a CSPRNG so the guaranteed characters are not first.
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def entropy_bits(length, pool_size):
    """log2(pool ^ length): the bits an attacker must guess."""
    return length * math.log2(pool_size)


def strength(bits):
    """Plain-English rating for an entropy value (NIST-style bands)."""
    if bits < 40:
        return "Weak"
    if bits < 60:
        return "Fair"
    if bits < 80:
        return "Strong"
    if bits < 100:
        return "Very strong"
    return "Excellent"


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate cryptographically secure passwords."
    )
    parser.add_argument("--length", type=int, default=16,
                        help="password length (default: 16)")
    parser.add_argument("--count", type=int, default=1,
                        help="how many passwords to generate (default: 1)")
    parser.add_argument("--no-lowercase", action="store_true",
                        help="exclude lowercase letters")
    parser.add_argument("--no-uppercase", action="store_true",
                        help="exclude uppercase letters")
    parser.add_argument("--no-digits", action="store_true",
                        help="exclude digits")
    parser.add_argument("--no-symbols", action="store_true",
                        help="exclude symbols")
    parser.add_argument("--exclude-ambiguous", action="store_true",
                        help="exclude look-alike characters (l, 1, I, O, 0)")
    parser.add_argument("--json", action="store_true",
                        help="print results as JSON instead of text")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    sets = build_sets(args)

    if not sets:
        print("error: every character set is disabled; nothing to draw "
              "from.", file=sys.stderr)
        return 2
    if args.length < len(sets):
        print(f"error: length {args.length} is shorter than the "
              f"{len(sets)} selected character sets; each set needs at "
              f"least one character.", file=sys.stderr)
        return 2
    if args.count < 1:
        print("error: --count must be at least 1.", file=sys.stderr)
        return 2

    pool_size = sum(len(chars) for chars in sets.values())
    bits = entropy_bits(args.length, pool_size)

    passwords = [generate_password(args.length, sets)
                 for _ in range(args.count)]

    if args.json:
        print(json.dumps({
            "passwords": passwords,
            "length": args.length,
            "pool_size": pool_size,
            "entropy_bits": round(bits, 1),
            "strength": strength(bits),
        }, indent=2))
        return 0

    for password in passwords:
        print(password)
    print(f"\nEntropy: {bits:.1f} bits ({strength(bits)}) "
          f"- pool of {pool_size} characters, length {args.length}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
