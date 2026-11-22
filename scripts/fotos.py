#!/usr/bin/env python3
"""Holt typische, frei lizenzierte Fotos je Region von Wikimedia Commons.

- nur Querformat, mind. 1600 px breit, Lizenzen CC0 / Public Domain / CC BY / CC BY-SA
- Bilder werden in photos/<slug>/ gespeichert (keine Datenübertragung an Wikimedia beim Seitenaufruf)
- Urheber und Lizenz landen in photos/<slug>.json und erscheinen im Seitenfuß

Aufruf: python scripts/fotos.py            (nur Portale ohne Fotos)
        python scripts/fotos.py --neu sylt  (Fotos für sylt neu holen)
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import config

ROOT = Path(__file__).resolve().parent.parent
API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia wünscht einen User-Agent mit Kontakt; Kontakt optional über Umgebungsvariable FOTO_KONTAKT
UA = "bnb-portale/1.0 (https://github.com/friesh-stack" + (f"; {os.environ['FOTO_KONTAKT']}" if os.environ.get("FOTO_KONTAKT") else "") + ")"
ERLAUBT = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+)", re.I)
PRO_PORTAL = 6


def hole(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def suche(begriff):
    q = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
         "gsrsearch": f"{begriff} filetype:bitmap", "gsrlimit": 15, "prop": "imageinfo",
         "iiprop": "url|size|extmetadata", "iiurlwidth": 1600}
    daten = json.loads(hole(API + "?" + urllib.parse.urlencode(q)))
    seiten = sorted(daten.get("query", {}).get("pages", {}).values(), key=lambda s: s.get("index", 99))
    for s in seiten:
        ii = (s.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lizenz = meta.get("LicenseShortName", {}).get("value", "")
        if not ERLAUBT.match(lizenz):
            continue
        if ii.get("width", 0) < 1600 or ii.get("width", 0) < ii.get("height", 0) * 1.2:
            continue
        autor = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", ""))).strip()[:80]
        yield {
            "quelle_url": ii.get("thumburl") or ii["url"],
            "seite": ii.get("descriptionurl", ""),
            "titel": re.sub(r"^File:|\.[a-z]+$", "", s["title"], flags=re.I),
            "autor": autor or "unbekannt",
            "lizenz": lizenz,
            "lizenz_url": meta.get("LicenseUrl", {}).get("value", ""),
        }


def fotos_fuer(p):
    ordner = ROOT / "photos" / p["slug"]
    ordner.mkdir(parents=True, exist_ok=True)
    liste, gesehen = [], set()
    begriffe = p.get("foto_suche", [])
    for runde in range(2):  # erst je Begriff das beste Foto, dann auffüllen
        for b in begriffe:
            if len(liste) >= PRO_PORTAL:
                break
            try:
                treffer = [t for t in suche(b) if t["seite"] not in gesehen]
            except Exception as e:  # noqa: BLE001
                print(f"  ! Suche '{b}' fehlgeschlagen: {e}")
                continue
            if treffer:
                t = treffer[0]
                gesehen.add(t["seite"])
                nr = len(liste) + 1
                (ordner / f"{nr}.jpg").write_bytes(hole(t.pop("quelle_url")))
                t["datei"] = f"fotos/{p['slug']}/{nr}.jpg"
                liste.append(t)
                print(f"  ✓ {t['titel'][:60]}  ({t['lizenz']})")
            time.sleep(0.5)
    (ROOT / "photos" / f"{p['slug']}.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv):
    neu = "--neu" in argv
    slugs = [a for a in argv if not a.startswith("--")]
    cfg = config.lade(mit_umleitungen=False)
    for p in cfg["portale"]:
        if slugs and p["slug"] not in slugs:
            continue
        if (ROOT / "photos" / f"{p['slug']}.json").exists() and not neu:
            continue
        print(f"Fotos für {p['slug']} …")
        fotos_fuer(p)


if __name__ == "__main__":
    main(sys.argv[1:])
