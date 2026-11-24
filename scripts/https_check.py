#!/usr/bin/env python3
"""Prüft alle GitHub-Pages-Seiten von friesh-stack mit eigener Domain auf „Enforce HTTPS“.
Aufruf: python scripts/https_check.py            (nur prüfen)
        python scripts/https_check.py --erzwingen (wo möglich einschalten)"""
import json, os, sys, urllib.request, urllib.error

def gh(m, p, d=None):
    r = urllib.request.Request("https://api.github.com" + p, method=m, data=json.dumps(d).encode() if d else None,
        headers={"Authorization": "Bearer " + os.environ["GH_PAT"], "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"_fehler": e.code, "_text": e.read().decode()[:200]}

erzwingen = "--erzwingen" in sys.argv
neu = [a for a in sys.argv[1:] if not a.startswith("-")]
weg = [a[1:] for a in sys.argv[1:] if a.startswith("-") and not a.startswith("--")]  # -repo = Domain entfernen  # Repos, deren Zertifikat neu angefordert wird
import time
repos, seite = [], 1
while True:
    r = gh("GET", f"/user/repos?per_page=100&page={seite}&affiliation=owner")
    if not r: break
    repos += r; seite += 1
zeilen = []
for r in sorted(repos, key=lambda x: x["name"].lower()):
    if not r.get("has_pages"): continue
    p = gh("GET", f"/repos/{r['full_name']}/pages")
    if not p.get("cname"): continue
    if r["name"] in weg:
        x = gh("PUT", f"/repos/{r['full_name']}/pages", {"cname": None})
        print("✂ Domain entfernt:", p["cname"], "aus", r["name"], "" if "_fehler" not in x else x); continue
    if r["name"] in neu:
        cn = p["cname"]; gh("PUT", f"/repos/{r['full_name']}/pages", {"cname": None}); time.sleep(5)
        gh("PUT", f"/repos/{r['full_name']}/pages", {"cname": cn}); time.sleep(3)
        p = gh("GET", f"/repos/{r['full_name']}/pages"); print("↻ Zertifikat neu angefordert:", cn)
    cert = (p.get("https_certificate") or {}).get("state", "–")
    ok = p.get("https_enforced")
    st = "✅ an" if ok else "❌ aus"
    if not ok and erzwingen:
        x = gh("PUT", f"/repos/{r['full_name']}/pages", {"cname": p["cname"], "https_enforced": True})
        st = "✅ jetzt eingeschaltet" if "_fehler" not in x else f"❌ geht noch nicht ({x['_text'][:80]})"
    zeilen.append(f"| {p['cname']} | {r['name']} | {cert} | {st} |")
print("| Domain | Repo | Zertifikat | Enforce HTTPS |\n|---|---|---|---|\n" + "\n".join(zeilen))
