"""Entry point used by the frozen Windows build."""

import sys

from gamecenter.cli import main

if __name__ == "__main__":
    sys.exit(main())
