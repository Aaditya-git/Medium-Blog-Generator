import yaml
from pathlib import Path
def main():
    cfg = yaml.safe_load((Path(__file__).resolve().parent.parent/'config'/'app.yaml').read_text())
    outdir = Path(cfg['paths']['local_output'])
    outdir.mkdir(parents=True, exist_ok=True)
    folder = outdir/'demo_post'
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'draft.md').write_text('# Demo Post\nGenerated locally.', encoding='utf-8')
    print('Artifacts saved to:', folder)
if __name__ == '__main__':
    main()
