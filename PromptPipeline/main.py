"""Entry point: reads a support ticket from inputs/ and runs the pipeline."""

import sys
import os
from app.pipeline import run_pipeline


def main() -> None:
    """Read ticket file from inputs/ and run the full 3-stage pipeline."""
    ticket_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join("inputs", "sample_ticket.txt")

    if not os.path.exists(ticket_file):
        print(f"Error: ticket file not found: {ticket_file}")
        sys.exit(1)

    with open(ticket_file, "r", encoding="utf-8") as f:
        ticket = f.read()

    run_pipeline(ticket)


if __name__ == "__main__":
    main()
