"""Rewrite clip URLs and config for a GitHub org. Usage: python set_base_url.py <org> [clips-a-repo] [clips-b-repo]"""
import sys, json, os, re
org = sys.argv[1]; ra = sys.argv[2] if len(sys.argv) > 2 else "clips-a"; rb = sys.argv[3] if len(sys.argv) > 3 else "clips-b"
here = os.path.dirname(os.path.abspath(__file__)); idx_path = os.path.join(here, "docs", "clips_index.json")
idx = json.load(open(idx_path)); split = {}
for cid, url in idx.items():
    repo = ra if ("clips-a" in url or "hatsim-clips-a" in url) else rb
    idx[cid] = f"https://{org}.github.io/{repo}/{cid}.mp4"
json.dump(idx, open(idx_path, "w"), indent=0)
cfg_path = os.path.join(here, "docs", "config.js"); cfg = open(cfg_path, encoding="utf-8").read()
cfg = re.sub(r'CLIPS_BASE: "[^"]*"', f'CLIPS_BASE: "https://{org}.github.io/{ra}/"', cfg); open(cfg_path, "w", encoding="utf-8").write(cfg)
print("rewritten", len(idx), "clip URLs ->", f"https://{org}.github.io/{{{ra},{rb}}}/")
