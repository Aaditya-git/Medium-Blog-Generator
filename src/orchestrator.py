import yaml
import argparse
from pathlib import Path
from .stages.input_stage import run as input_run
from .stages.research_stage import run as research_run
from .stages.outline_stage import run as outline_run
from .stages.draft_stage import run as draft_run
from .stages.review_stage import run as review_run
from .stages.archive_stage import run as archive_run
from .stages.finalize_stage import run as finalize_run
from .utils.io import run_folder, finalize_folder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('topic', type=str)
    parser.add_argument('--tone', type=str, default=None)
    args = parser.parse_args()

    # Load config
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / 'config' / 'app.yaml').read_text(encoding='utf-8'))
    outputs_root = Path(cfg['paths']['local_output']).resolve()
    published_root = Path(cfg['paths'].get('published_root','./run/PUBLISHED')).resolve()

    # 1) Input
    ctx = input_run(args.topic, args.tone)
    out_folder = run_folder(outputs_root, ctx.date_slug, ctx.topic_slug)

    # 2) Research
    research = research_run(ctx.topic)

    # 3) Outline
    outline = outline_run(ctx.topic, research.sources)

    # 4) Draft
    draft = draft_run(outline.title, outline.standfirst, outline.hook, outline.sections, research.sources)

    # 5) Review
    review = review_run(draft.markdown)
    if not review.ok:
        # still archive what we have
        archive_run(out_folder, draft.markdown, [f\"DRAFT FAILED REVIEW: {review.notes}\"])
        print(f\"Review failed: {review.notes}\")
        return 1

    # 6) Archive
    refs_list = [f\"[{c['n']}] {c['title']} — {c['url']} (accessed: {c['accessed_at']})\" for c in draft.citations]
    archive_run(out_folder, draft.markdown, refs_list)

    print(f\"Artifacts saved to: {out_folder}\")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
