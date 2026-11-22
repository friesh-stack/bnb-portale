"""Gemeinsames Laden von portale.json für alle Skripte.

- "aktiv": false        → Portal ist pausiert und wird überall übersprungen
- "zusatz_domains": [...] → jede Zusatz-Domain bekommt ein eigenes Mini-Repo (Name = Domain),
                            das per GitHub Pages + HTTPS auf die Hauptdomain weiterleitet
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lade(mit_umleitungen=False):
    cfg = json.loads((ROOT / "portale.json").read_text(encoding="utf-8"))
    portale = [p for p in cfg["portale"] if p.get("aktiv", True)]
    if mit_umleitungen:
        extra = []
        for p in portale:
            for d in p.get("zusatz_domains", []):
                extra.append({"slug": f"{p['slug']}~{d}", "domain": d, "repo": d, "modus": "neu",
                              "allinkl": "dns", "umleitung": True, "ziel": p["domain"], "marke": p["marke"]})
        portale = portale + extra
    cfg["portale"] = portale
    return cfg
