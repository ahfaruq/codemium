#!/usr/bin/env python3
"""Render a Codemium benchmark dashboard as SVG + Markdown.

Publication rule: --publish refuses non-measured datasets.
"""
from __future__ import annotations
import argparse, html, json, statistics
from pathlib import Path

METRICS = [("loc_changed","LOC"),("total_tokens","tokens"),("cost_usd","cost"),("seconds","time")]
COLORS = ["#9aa4b0","#33b75b","#1f9df0","#8a5cf5","#e58a25","#ef5da8"]

def load(path: Path):
    raw=json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw,list): return {"kind":"synthetic","title":"Legacy benchmark sample"},raw
    if not isinstance(raw,dict) or not isinstance(raw.get("runs"),list): raise SystemExit("benchmark JSON must be a run list or {meta,runs}")
    return raw.get("meta",{}),raw["runs"]

def token_total(row):
    if isinstance(row.get("total_tokens"),(int,float)): return float(row["total_tokens"])
    vals=[row.get(k) for k in ("input_tokens","reasoning_tokens","output_tokens")]
    return float(sum(vals)) if all(isinstance(v,(int,float)) for v in vals) else None

def value(row,key):
    if key=="total_tokens": return token_total(row)
    v=row.get(key); return float(v) if isinstance(v,(int,float)) else None

def means(runs):
    groups={}
    for r in runs: groups.setdefault(str(r["system"]),[]).append(r)
    out={}
    for system,rows in groups.items():
        d={"n":len(rows)}
        for key,_ in METRICS:
            vals=[value(r,key) for r in rows]; vals=[v for v in vals if v is not None]
            d[key]=statistics.mean(vals) if vals else None
        q=[r["quality_pass"] for r in rows if isinstance(r.get("quality_pass"),bool)]
        s=[r["safety_pass"] for r in rows if isinstance(r.get("safety_pass"),bool)]
        d["quality_pass_rate"]=sum(q)/len(q) if q else None
        d["safety_pass_rate"]=sum(s)/len(s) if s else None
        out[system]=d
    return out

def fmt_base(key,v):
    if v is None:return "n/a"
    if key=="cost_usd":return f"${v:.3f}"
    if key=="seconds":return f"{v:.0f}s"
    if key=="total_tokens":return f"{v/1000:.0f}k" if v>=1000 else f"{v:.0f}"
    return f"{v:.0f}"

def pct(v,base): return None if v is None or base in (None,0) else v/base*100.0

def esc(s): return html.escape(str(s))

def svg(meta,stats,baseline,out:Path):
    if baseline not in stats: raise SystemExit(f"baseline system {baseline!r} not present")
    systems=list(stats); systems.remove(baseline); systems.insert(0,baseline)
    width,height=1280,810; left,top,chart_w,chart_h=95,235,1100,360; group_w=chart_w/len(METRICS); max_pct=125.0
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="#080b10"/>','<style>text{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Arial;fill:#f5f7fa}.muted{fill:#9ca8b7}.grid{stroke:#29313d;stroke-width:1}.base{stroke:#7b8794;stroke-dasharray:6 6}.title{font-weight:700}.small{font-size:13px}.label{font-size:15px}</style>','<text x="50" y="54" class="title" font-size="32">Numbers</text>','<line x1="50" y1="72" x2="1230" y2="72" stroke="#818896"/>']
    kind=meta.get("kind","synthetic"); title=meta.get("title","Codemium agent benchmark"); repo=meta.get("repository","unspecified repository"); agent=meta.get("agent","unspecified agent"); model=meta.get("model","unspecified model"); n=meta.get("runs_per_arm")
    subtitle=f"{title} — {repo}; {agent}; {model}"+(f"; n={n}" if n else "")
    parts.append(f'<text x="50" y="115" font-size="18">{esc(subtitle)}</text>')
    if kind!="measured": parts += ['<rect x="50" y="135" width="1180" height="44" rx="8" fill="#5b2b00" stroke="#ff9b36"/>','<text x="70" y="163" font-size="17" fill="#ffd19b">SYNTHETIC / DEMO DATA — NOT CODEMIUM PRODUCT PERFORMANCE</text>']
    lx=285
    for i,s in enumerate(systems):
        x=lx+i*190; parts += [f'<rect x="{x}" y="194" width="16" height="16" rx="3" fill="{COLORS[i%len(COLORS)]}"/>',f'<text x="{x+24}" y="207" class="small">{esc(s)}</text>']
    for tick in [0,25,50,75,100,125]:
        y=top+chart_h-(tick/max_pct)*chart_h; cls="base" if tick==100 else "grid"
        parts += [f'<line x1="{left}" y1="{y:.1f}" x2="{left+chart_w}" y2="{y:.1f}" class="{cls}"/>',f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" class="muted small">{tick}%</text>']
    bar_gap=8; usable=group_w-55; bar_w=min(42,(usable-bar_gap*(len(systems)-1))/max(1,len(systems)))
    for mi,(key,label) in enumerate(METRICS):
        gx=left+mi*group_w+28; base=stats[baseline].get(key)
        for si,s in enumerate(systems):
            p=pct(stats[s].get(key),base); x=gx+si*(bar_w+bar_gap)
            if p is None: parts.append(f'<text x="{x+bar_w/2:.1f}" y="{top+chart_h-8}" text-anchor="middle" class="muted small">n/a</text>'); continue
            clipped=min(max(p,0),max_pct); h=(clipped/max_pct)*chart_h; y=top+chart_h-h; c=COLORS[si%len(COLORS)]
            parts += [f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="3" fill="{c}"/>',f'<text x="{x+bar_w/2:.1f}" y="{max(y-8,top+12):.1f}" text-anchor="middle" font-size="13" fill="{c}">{p:.0f}%</text>']
        center=left+mi*group_w+group_w/2; parts += [f'<text x="{center:.1f}" y="{top+chart_h+32}" text-anchor="middle" font-size="18">{label}</text>',f'<text x="{center:.1f}" y="{top+chart_h+53}" text-anchor="middle" class="muted small">base {esc(fmt_base(key,base))}</text>']
    yq=665; parts += [f'<line x1="75" y1="{yq-28}" x2="1205" y2="{yq-28}" class="grid"/>',f'<text x="75" y="{yq}" class="muted small">Quality / safety gates (higher is better):</text>']
    xx=330
    for i,s in enumerate(systems):
        q=stats[s].get("quality_pass_rate"); sa=stats[s].get("safety_pass_rate"); txt=f'{s}: quality {q*100:.0f}%' if q is not None else f'{s}: quality n/a'; txt+=f' · safe {sa*100:.0f}%' if sa is not None else ' · safe n/a'; parts.append(f'<text x="{xx}" y="{yq}" class="small" fill="{COLORS[i%len(COLORS)]}">{esc(txt)}</text>'); xx+=280
    yt=720; parts.append(f'<text x="75" y="{yt}" class="title" font-size="17">vs {esc(baseline)} baseline</text>'); xx=365
    for key,label in METRICS: parts.append(f'<text x="{xx}" y="{yt}" class="muted small">{label}</text>'); xx+=160
    yy=748
    for si,s in enumerate(systems[1:]):
        parts.append(f'<text x="75" y="{yy}" class="label" fill="{COLORS[(si+1)%len(COLORS)]}">{esc(s)}</text>'); xx=365
        for key,_ in METRICS:
            p=pct(stats[s].get(key),stats[baseline].get(key)); txt="n/a" if p is None else f'{p-100:+.0f}%'; parts.append(f'<text x="{xx}" y="{yy}" class="label">{txt}</text>'); xx+=160
        yy+=28
    parts.append('</svg>'); out.write_text("\n".join(parts),encoding="utf-8")

def markdown(meta,stats,baseline,svg_path):
    systems=list(stats); kind=meta.get("kind","synthetic"); lines=["# Numbers",""]
    lines += (["> **Synthetic/demo data only. This is not Codemium product performance.**",""] if kind!="measured" else ["> These numbers come from measured agent runs. Lower is better for LOC/tokens/cost/time; higher is better for quality/safety.",""])
    lines += [f"![Codemium benchmark chart]({svg_path})","",f"| vs {baseline} baseline | LOC | tokens | cost | time | quality | safe |","| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in systems:
        if s==baseline: continue
        vals=[]
        for key,_ in METRICS:
            p=pct(stats[s].get(key),stats[baseline].get(key)); vals.append("n/a" if p is None else f"{p-100:+.0f}%")
        q=stats[s].get("quality_pass_rate"); sa=stats[s].get("safety_pass_rate"); vals += ["n/a" if q is None else f"{q*100:.0f}%","n/a" if sa is None else f"{sa*100:.0f}%"]
        lines.append("| "+s+" | "+" | ".join(vals)+" |")
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--baseline",default="vanilla"); ap.add_argument("--svg",default="benchmarks/numbers.svg"); ap.add_argument("--markdown",default="benchmarks/NUMBERS.md"); ap.add_argument("--publish",action="store_true",help="Refuse unless meta.kind == measured"); ns=ap.parse_args()
    meta,runs=load(Path(ns.data))
    if ns.publish and meta.get("kind")!="measured": raise SystemExit("refusing publication: meta.kind must be 'measured'")
    stats=means(runs); svg_out=Path(ns.svg); svg_out.parent.mkdir(parents=True,exist_ok=True); md_out=Path(ns.markdown); md_out.parent.mkdir(parents=True,exist_ok=True); svg(meta,stats,ns.baseline,svg_out); md_out.write_text(markdown(meta,stats,ns.baseline,svg_out.name),encoding="utf-8"); print(json.dumps({"kind":meta.get("kind","synthetic"),"systems":stats,"svg":str(svg_out),"markdown":str(md_out)},indent=2))
if __name__=="__main__": main()
