"""Pipeline orchestrator: runs the 3-stage customer support ticket pipeline."""

from datetime import datetime
from app.stage1_understand import stage1_understand
from app.stage2_reason import stage2_reason
from app.stage3_produce import stage3_produce
from app.utils import print_stage, save_output


def run_pipeline(ticket: str) -> dict:
    """Run the full 3-stage customer support ticket pipeline.

    Stages:
        1. Understand — extract structured fields from the raw ticket.
        2. Reason     — determine priority, routing, and chain-of-thought.
        3. Produce    — draft an on-brand reply (≤120 words, no false promises).

    Args:
        ticket: Raw customer support ticket text.

    Returns:
        Dictionary with all stage outputs and the final drafted reply.
    """
    print("\n🚀 Starting customer support ticket pipeline...\n")

    # Stage 1 — Extract ticket fields
    stage1_output = stage1_understand(ticket)
    print_stage("STAGE 1 — Understand: Extracted Ticket Fields", stage1_output)

    # Stage 2 — Priority + routing + reasoning
    stage2_output = stage2_reason(stage1_output)
    print_stage("STAGE 2 — Reason: Priority & Routing", stage2_output)

    # Stage 3 — Draft customer reply
    reply = stage3_produce(stage1_output, stage2_output)
    print("\n" + "=" * 60)
    print("  STAGE 3 — Produce: Drafted Reply")
    print("=" * 60)
    print(reply)

    # Save combined output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "ticket_fields": stage1_output,
        "priority_routing": stage2_output,
        "drafted_reply": reply,
    }
    saved_path = save_output(f"result_{timestamp}.json", result)
    print(f"\n✅ Pipeline complete. Output saved to: {saved_path}\n")

    return result
