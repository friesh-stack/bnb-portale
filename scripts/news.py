#!/usr/bin/env python3
"""Aktualisiert die Meldungen „Aktuell“ je Portal über die Claude-API mit Websuche.

- Rhythmus je Portal aus portale.json: "taeglich" oder "woechentlich"
- Ergebnis: content/<slug>.json  (wird von build.py in die AUTO:news-Zone geschrieben)
- Regeln: eigene Worte, 2–3 Sätze, Quelle verlinkt, nichts erfinden, keine abgelaufenen Termine

Umgebung: ANTHROPIC_API_KEY (Pflicht), CLAUDE_MODEL (optional)
Aufruf:   python scripts/news.py            (alle fälligen)
          python scripts/news.py --alle     (alle sofort)
          python scripts/news.py hamburg    (nur dieses Portal)
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import config

ROOT = Path(__file__).resolve().parent.parent
MODELL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
HEUTE = dt.date.today()
SPRACHNAMEN = {"de": "Deutsch", "en": "Englisch", "it": "Italienisch", "fr": "Französisch", "es": "Spanisch", "nl": "Niederländisch", "da": "Dänisch", "sv": "Schwedisch", "nb": "Norwegisch (Bokmål)", "fi": "Finnisch", "zh": "Chinesisch (vereinfacht)"}


def faellig(p):
    datei = ROOT / "content" / f"{p['slug']}.json"
    if not datei.exists():
        return True
    try:
        stand = dt.date.fromisoformat(json.loads(datei.read_text(encoding="utf-8")).get("stand", "2000-01-01"))
    except ValueError:
        return True
    tage = 1 if p.get("news") == "taeglich" else 7
    return (HEUTE - stand).days >= tage


def _api(body):
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            antwort = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:400]}") from None
    return "".join(b.get("text", "") for b in antwort.get("content", []) if b.get("type") == "text")


def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Keine JSON-Antwort: " + text[:300])
    return json.loads(m.group(0))


def frage_claude(prompt):
    text = _api({
        "model": MODELL,
        "max_tokens": 12000,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
        "messages": [{"role": "user", "content": prompt}],
    })
    try:
        return _json(text)
    except ValueError:  # json.JSONDecodeError ist ein ValueError – einmal reparieren lassen
        repariert = _api({
            "model": MODELL,
            "max_tokens": 12000,
            "messages": [{"role": "user", "content":
                          "Repariere dieses JSON, sodass es gültig ist (Anführungszeichen in Texten escapen oder durch typografische ersetzen). "
                          "Inhalt nicht ändern. Antworte NUR mit dem JSON:\n\n" + text}],
        })
        return _json(repariert)


def prompt_fuer(p):
    region = p["region"].get("de") or next(iter(p["region"].values()))
    sprachen = ", ".join(f'"{s}" ({SPRACHNAMEN[s]})' for s in p["sprachen"])
    zeitraum = "heute und die nächsten 7 Tage" if p.get("news") == "taeglich" else "die nächsten 14 Tage"
    return f"""Du pflegst die Rubrik „Aktuell“ des Gästeportals {p['domain']} für Urlauber in {region}.
Heute ist der {HEUTE.isoformat()}. Suche im Web nach Meldungen, die für Touristen in {region} für {zeitraum} relevant sind:
Veranstaltungen, Märkte, Ausstellungen, Feste, Verkehr/Fähren/Bahn-Einschränkungen, Wetter- oder Strandhinweise, neue Angebote.
Suchhinweise: {p.get('news_suche', region)}

Regeln:
- 3 bis 5 Meldungen, nur mit echter, verlinkbarer Quelle aus deinen Suchergebnissen. Nichts erfinden, keine Vermutungen.
- In eigenen Worten, je 2–3 kurze Sätze, sachlich und freundlich. Keine wörtlichen Zitate über 10 Wörter.
- Keine Werbung für Konkurrenzportale, keine politischen Themen, keine Unglücke/Kriminalität.
- Abgelaufene Termine weglassen. Gib für Termine "bis" (letzter Tag) an.
- Titel und Text in diesen Sprachen: {sprachen}.
- Innerhalb von Titeln und Texten KEINE geraden Anführungszeichen (") verwenden – nur typografische („“ «»).

Antworte NUR mit diesem JSON, ohne weiteren Text:
{{"items":[{{"datum":"YYYY-MM-DD","bis":"YYYY-MM-DD oder leer","titel":{{"de":"..."}},"text":{{"de":"..."}},"quelle":"https://...","quelle_name":"Name der Website"}}]}}"""


def main(argv):
    alle = "--alle" in argv
    slugs = [a for a in argv if not a.startswith("--")]
    cfg = config.lade(mit_umleitungen=False)
    (ROOT / "content").mkdir(exist_ok=True)
    fehler = 0
    for p in cfg["portale"]:
        if slugs and p["slug"] not in slugs:
            continue
        if not (alle or slugs or faellig(p)):
            continue
        print(f"News für {p['slug']} …")
        try:
            daten = frage_claude(prompt_fuer(p))
            items = [i for i in daten.get("items", []) if str(i.get("quelle", "")).startswith("http")]
            items = [i for i in items if not i.get("bis") or i["bis"] >= HEUTE.isoformat()]
            for i in items:
                for feld in ("titel", "text"):
                    if isinstance(i.get(feld), str):
                        i[feld] = {p["sprachen"][0]: i[feld]}
            (ROOT / "content" / f"{p['slug']}.json").write_text(
                json.dumps({"stand": HEUTE.isoformat(), "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  ✓ {len(items)} Meldungen")
        except Exception as e:  # noqa: BLE001 – ein Portal darf die anderen nicht blockieren
            fehler += 1
            print(f"  ! Fehler: {e}")
    # News-Fehler blockieren nie den Rest (Bauen, Hochladen, All-Inkl)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
