"""
Shared .env loader for all 42: Python scripts.

Searches for .env in this order:
1. Current working directory (./.env)
2. Output root (references/../.env)
3. Home config (~/.config/42-seo/.env)
4. Legacy seo-agi config (~/.config/seo-agi/.env)

Usage in any 42: script:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "references"))
    from load_env import load_env
    load_env()
    # Now os.environ has all keys from .env

Or simpler — just call at the top of main():
    load_env()
"""

import os
from pathlib import Path


def load_env(verbose: bool = False) -> dict[str, str]:
    """Load .env file into os.environ. Returns dict of loaded keys.

    Does NOT override existing environment variables — env vars set in the
    shell take precedence over .env file values. This matches the standard
    dotenv convention.
    """
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",  # output/.env
        Path.home() / ".config" / "42-seo" / ".env",
        Path.home() / ".config" / "seo-agi" / ".env",     # legacy
    ]

    loaded = {}
    env_file = None

    for path in search_paths:
        if path.is_file():
            env_file = path
            break

    if not env_file:
        if verbose:
            import sys
            print("No .env file found. Searched:", file=sys.stderr)
            for p in search_paths:
                print(f"  {p}", file=sys.stderr)
        return loaded

    if verbose:
        import sys
        print(f"Loading .env from {env_file}", file=sys.stderr)

    with open(env_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Don't override existing env vars
            if key and key not in os.environ:
                os.environ[key] = value
                loaded[key] = value

    if verbose:
        import sys
        print(f"Loaded {len(loaded)} env vars: {', '.join(loaded.keys())}", file=sys.stderr)

    return loaded


# Auto-load when imported
_loaded = load_env()
