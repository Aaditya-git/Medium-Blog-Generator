import yaml
import argparse
from pathlib import Path
from .stages.input_stage import run as input_run
from .stages.research_stage import run as research_run
from .stages.outline_stage import run as outline_run
from .stages.draft_stage import run as draft_run
from .stages.review_stage import run as review_run
from .stages.archive_stage import run as archive_run
from .utils.io import run_folder

def _save_research_file(out_folder: Path, research):
    lines = ["# Research Notes", "", "## Queries"]
    lines += [f"- {q}" for q in research.queries]
    lines += ["", "## Candidate Sources"]
    for s in research.sources:
        lines.append(f"[{s['n']}] {s['title']} — {s['url']} (published: {s.get('published','?')}, accessed: {s.get('accessed','?')})")
        if s.get("notes"):
            for n in s["notes"]:
                lines.append(f"  - {n}")
    (out_folder / "research.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def _save_outline_file(outline_folder: Path, outline):
    lines = [f"# {outline.title}", f"*{outline.standfirst}*", "", outline.hook, ""]
    for sec in outline.sections:
        lines.append(f"## {sec['h2']}")
        for b in sec.get("bullets", []):
            lines.append(f"- {b}")
        lines.append("")
    (outline_folder / "outline.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", type=str)
    parser.add_argument("--tone", type=str, default=None)
    args = parser.parse_args()

    cfg_path = Path(__file__).resolve().parents[1] / "config" / "app.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    outputs_root = Path(cfg["paths"]["local_output"]).resolve()

    # 1) Input
    ctx = input_run(args.topic, args.tone)
    out_folder = run_folder(outputs_root, ctx.date_slug, ctx.topic_slug)

    # 2) Research (saved to research.md)
    research = research_run(ctx.topic)
    _save_research_file(out_folder, research)

    # 3) Outline (saved to outline.md)
    outline = outline_run(ctx.topic, research.sources)
    _save_outline_file(out_folder, outline)

    # 4) Draft (long-form markdown)
    draft = draft_run(
        outline.title,
        outline.standfirst,
        outline.hook,
        outline.sections,
        research.sources,
        tone=ctx.tone
    )

    # 5) Review
    review = review_run(draft.markdown)
    if not review.ok:
        archive_run(out_folder, draft.markdown, [f"DRAFT FAILED REVIEW: {review.notes}"])
        print(f"Review failed: {review.notes}")
        return 1

    # 6) Archive (writes draft.md + references.txt)
    refs_list = [
        f"[{c['n']}] {c['title']} — {c['url']} (accessed: {c['accessed_at']})"
        for c in draft.citations
    ]
    archive_run(out_folder, draft.markdown, refs_list)

    print("The research, outline, and draft have been created and saved to:")
    print(str(out_folder))
    print("The folder contains:\n- research.md\n- outline.md\n- draft.md\n- references.txt")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
