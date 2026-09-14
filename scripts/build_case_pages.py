"""Render the authored case studies as readable static gallery pages."""
from pathlib import Path
import html
import re

root=Path(__file__).resolve().parents[1]
for project in ['remittance','leads','guests','orders']:
    source=(root/'projects'/project/'CASE-STUDY.md').read_text(encoding='utf-8')
    blocks=[]
    for block in source.strip().split('\n\n'):
        level=2 if block.startswith('## ') else 1 if block.startswith('# ') else 0
        clean=html.escape(block[(level+1):] if level else block)
        clean=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',clean)
        blocks.append(f'<h{level}>{clean}</h{level}>' if level else f'<p>{clean}</p>')
    target=root/'site'/'projects'/project;target.mkdir(parents=True,exist_ok=True)
    title=html.escape(source.splitlines()[0][2:])
    output=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
body{{font:16px/1.8 'Segoe UI',Arial,sans-serif;background:#f3f6f4;color:#253f39;margin:0}}main{{max-width:850px;margin:40px auto;background:#fff;border:1px solid #dae5df;border-radius:12px;padding:42px}}h1{{font-size:34px;line-height:1.2;letter-spacing:-1px}}h2{{font-size:17px;margin-top:28px}}p{{color:#5f756d;font-size:14px}}a{{color:#0c7763}}img,video{{width:100%;border-radius:8px}}small{{font-size:11px;color:#71827b}}@media(max-width:600px){{main{{padding:24px;margin:12px}}h1{{font-size:27px}}}}
</style></head><body><main><a href="../../">← Portfolio gallery</a>{''.join(blocks)}<h2>Actual application walkthrough</h2><video controls preload="metadata" src="assets/walkthrough.mp4" poster="assets/01-dashboard.png"></video><small>Captioned actual-app captures. Synthetic data. Simulated external providers.</small><h2>Dashboard</h2><a href="assets/01-dashboard.png"><img src="assets/01-dashboard.png" alt="Actual dashboard for {title}" loading="lazy"></a><p><a href="https://github.com/metehanbergin/automation-portfolio/tree/main/projects/{project}">Source, setup and demonstration script ↗</a></p></main></body></html>'''
    (target/'case-study.html').write_text(output,encoding='utf-8')
print('Rendered four case-study pages.')
