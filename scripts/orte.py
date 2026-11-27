"""Wöchentlich: Orte für die Strategiespiele holen und als content/orte/<repo>.json ablegen
(build.py kopiert sie als orte.json ins Portal).
- Stadt-Spiele (Hamburg, Rügen, München): OpenStreetMap-Auszug von Geofabrik, ausgewertet mit osmium – alles inkl. Bus und Supermärkte.
- Länder-Spiele: bekannte Orte aus Wikidata (SPARQL), sortiert nach Bekanntheit. Details lädt das Spiel beim Heranzoomen live.
Aufruf: python scripts/orte.py [--neu] [slug ...]"""
import json, sys, time, subprocess, urllib.request, urllib.parse, datetime, tempfile
from pathlib import Path
import socket
_gai = socket.getaddrinfo  # GitHub-Runner haben zeitweise kein IPv6 – nur IPv4 verwenden
socket.getaddrinfo = lambda h, p, f=0, *a, **k: _gai(h, p, socket.AF_INET, *a, **k)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "orte"
UA = "friesh-stack-portale/1.0 (+https://github.com/friesh-stack)"
KEEP = ("cuisine", "website", "contact:website", "opening_hours", "addr:street", "addr:housenumber", "addr:city")
GRENZE = {"bus": 8000, "shop": 6000, "garden": 4000, "ita": 3000, "asia": 3000, "ger": 3000, "food": 4000}


# ---------------- Städte: Geofabrik + osmium ----------------
FILTER = ["nwr/tourism=attraction,museum,gallery,theme_park,zoo,aquarium,viewpoint", "nwr/historic=castle,monument,ruins,city_gate,fort",
          "nwr/railway=station,halt", "n/highway=bus_stop", "nwr/shop=mall,department_store,supermarket", "w/highway=pedestrian",
          "nwr/leisure=water_park,stadium,garden,park", "nwr/man_made=tower", "nwr/amenity=theatre,arts_centre,restaurant"]


import re
K_ITA = re.compile(r"italian|pizza")
K_ASIA = re.compile(r"chinese|japanese|thai|vietnamese|asian|sushi|korean|indian|ramen|nepalese|indonesian|malaysian|filipino|pakistani|noodle|dim_sum|bubble_tea|cantonese|sichuan")
K_GER = re.compile(r"german|bavarian|schnitzel|currywurst|austrian|regional")  # Stadt-Spiele liegen alle in Deutschland


def kat(t):
    n = t.get("name")
    if t.get("amenity") == "restaurant":
        if not n:
            return None
        c = t.get("cuisine", "")
        return "ita" if K_ITA.search(c) else "asia" if K_ASIA.search(c) else "ger" if K_GER.search(c) else "food"
    if t.get("highway") == "bus_stop":
        return "bus" if n else None
    if t.get("railway") in ("station", "halt"):
        return "rail" if n else None
    if t.get("tourism") in ("museum", "gallery"):
        return "museum" if n else None
    if t.get("shop") in ("mall", "department_store", "supermarket"):
        return "shop"
    if t.get("highway") == "pedestrian":
        return "shop" if n else None
    if t.get("tourism") in ("theme_park", "zoo", "aquarium") or t.get("leisure") == "water_park":
        return "fun"
    if t.get("leisure") == "stadium":
        return "stadium" if n else None
    if t.get("leisure") == "garden":
        return "garden" if t.get("garden:type") == "botanical" else None
    if t.get("leisure") == "park":
        return "garden" if n else None
    if t.get("tourism") == "viewpoint" or (t.get("man_made") == "tower" and t.get("tower:type") == "observation"):
        return "view"
    if t.get("amenity") in ("theatre", "arts_centre"):
        return "theatre" if n else None
    if (t.get("tourism") == "attraction" or t.get("historic")) and n:
        return "sight"
    return None


def mitte(g):
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(g["coordinates"])
    return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)


def stadt(sp):
    S, W, N, E = sp["bbox"]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); pbf = d / "a.osm.pbf"
        print("  lade", sp["pbf"]); t0 = time.time()
        req = urllib.request.Request(sp["pbf"], headers={"User-Agent": UA})
        for v in range(4):
            try:
                with urllib.request.urlopen(req, timeout=900) as r, open(pbf, "wb") as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b)
                break
            except Exception as e:
                if v == 3:
                    raise
                print("    Download-Fehler, neuer Versuch:", e); time.sleep(20 * (v + 1))
        print(f"  {pbf.stat().st_size // 2**20} MB in {time.time() - t0:.0f}s")
        subprocess.run(["osmium", "extract", "-b", f"{W},{S},{E},{N}", "-o", str(d / "b.osm.pbf"), str(pbf)], check=True)
        subprocess.run(["osmium", "tags-filter", "-o", str(d / "c.osm.pbf"), str(d / "b.osm.pbf")] + FILTER, check=True)
        subprocess.run(["osmium", "export", "-f", "geojsonseq", "--add-unique-id=type_id", "-o", str(d / "c.geojsonseq"), str(d / "c.osm.pbf")], check=True)
        erg, seen = {}, set()
        for line in open(d / "c.geojsonseq", encoding="utf-8"):
            line = line.strip().lstrip("\x1e")
            if not line:
                continue
            ft = json.loads(line); t = ft.get("properties") or {}
            k = kat(t)
            if not k or not ft.get("geometry"):
                continue
            uid = str(ft.get("id", ""))  # n123 / w456 / r789
            if uid in seen:
                continue
            seen.add(uid)
            lat, lon = mitte(ft["geometry"])
            if not (S <= lat <= N and W <= lon <= E):
                continue
            row = [round(lat, 5), round(lon, 5), t.get("name", ""), uid]
            ex = {x: t[x] for x in KEEP if x in t}
            if ex:
                row.append(ex)
            erg.setdefault(k, []).append(row)
        return {k: v[:GRENZE.get(k, 3000)] for k, v in erg.items()}


# ---------------- Länder: Wikidata ----------------
LAND_Q = dict(SE="Q34", NO="Q20", FI="Q33", DK="Q35", FR="Q142", ES="Q29", IT="Q38", PT="Q45", HU="Q28", AT="Q40", GR="Q41", CH="Q39")
WD_CLS = {
    "sight": "Q570116 Q23413 Q751876 Q4989906 Q16560 Q12518 Q57821 Q44539 Q16970",
    "museum": "Q33506 Q207694 Q16735822 Q756102 Q588140 Q1007870 Q17431399",
    "rail": "Q55488 Q1793804 Q928830",
    "shop": "Q11315 Q216107",
    "fun": "Q194195 Q43501 Q2281788 Q2416723",
    "stadium": "Q483110 Q1076486",
    "garden": "Q167346 Q22698 Q1107656",
    "view": "Q1440300 Q6017969",
    "theatre": "Q24354 Q153562 Q1060829",
}
WD_LIMIT = {"sight": 500, "museum": 400, "rail": 300, "shop": 150, "fun": 150, "stadium": 150, "garden": 300, "view": 200, "theatre": 250}


def sparql(q):
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    for v in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print("    Wikidata-Fehler:", e); time.sleep(15 * (v + 1))
    return None


def land(sp, sprachen):
    q_land = LAND_Q[sp["iso"]]; S, W, N, E = sp["bbox"]; erg = {}
    lang = ",".join(dict.fromkeys(sprachen + ["en"]))
    for k, cls in WD_CLS.items():
        vals = " ".join("wd:" + c for c in cls.split())
        q = f"""SELECT ?item ?itemLabel ?coord (SAMPLE(?w) AS ?web) (MAX(?s) AS ?sl) WHERE {{
  VALUES ?c {{ {vals} }} ?item wdt:P31 ?c; wdt:P17 wd:{q_land}; wdt:P625 ?coord; wikibase:sitelinks ?s.
  OPTIONAL {{ ?item wdt:P856 ?w. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }} }}
GROUP BY ?item ?itemLabel ?coord ORDER BY DESC(?sl) LIMIT {WD_LIMIT[k]}"""
        print(f"  {sp['iso']} · {k}"); t0 = time.time()
        b = sparql(q)
        if b is None:
            return None
        L, seen = [], set()
        for r in b:
            qid = r["item"]["value"].rsplit("/", 1)[1]
            if qid in seen:
                continue
            seen.add(qid)
            c = r["coord"]["value"]  # Point(lon lat)
            try:
                lon, lat = map(float, c[c.index("(") + 1:c.index(")")].split())
            except ValueError:
                continue
            if not (S <= lat <= N and W <= lon <= E):
                continue
            name = r.get("itemLabel", {}).get("value", "")
            if not name or name == qid:
                continue
            row = [round(lat, 5), round(lon, 5), name, "q" + qid[1:]]
            if "web" in r:
                row.append({"website": r["web"]["value"]})
            L.append(row)
        erg[k] = L
        print(f"    {len(L)} Orte in {time.time() - t0:.1f}s"); time.sleep(2)
    return erg


# ---------------- Top 10 je Kategorie (Wikidata) ----------------
TOP = {  # Kategorie: (Klassen, Kennzahl-Eigenschaft oder None, Name der Kennzahl)
    # Sehenswürdigkeiten: alle bekannten Bauwerke/Ziele zusammen (inkl. Konzerthaus, Rathaus, Brücken, Museen, Zoos), nach Bekanntheit
    "sight": (" ".join(dict.fromkeys((WD_CLS["sight"] + " " + WD_CLS["museum"] + " " + WD_CLS["fun"] + " " + WD_CLS["theatre"]
              + " Q1060829 Q543654 Q12280 Q2977 Q1440300 Q483110").split())), None, "sitelinks"),
    "museum": (WD_CLS["museum"], "P1174", "visitors"),
    "fun": (WD_CLS["fun"], "P1174", "visitors"),
    "view": ("Q1440300 Q6017969", "P2048", "height"),
    "stadium": (WD_CLS["stadium"], "P1083", "capacity"),
    "rail": (WD_CLS["rail"], "P1373", "patronage"),
    "shop": (WD_CLS["shop"], None, "sitelinks"),
    "garden": (WD_CLS["garden"], None, "sitelinks"),
    "theatre": (WD_CLS["theatre"], None, "sitelinks"),
}


STADT_Q = {"hamburg": "Q1055", "muenchen": "Q1726"}  # nur Orte innerhalb der Stadtgrenze


def ort_filter(sp, slug=""):
    if sp.get("stadt"):
        innen = f" ?item wdt:P131/wdt:P131?/wdt:P131?/wdt:P131? wd:{STADT_Q[slug]} ." if slug in STADT_Q else ""
        S, W, N, E = sp["bbox"]
        return f"""SERVICE wikibase:box {{ ?item wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point({W} {S})"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point({E} {N})"^^geo:wktLiteral . }}""" + innen
    return f"?item wdt:P17 wd:{LAND_Q[sp['iso']]}; wdt:P625 ?coord."


def top10(sp, sprachen, slug=""):
    lang = ",".join(dict.fromkeys(sprachen + ["de", "en"])); f = ort_filter(sp, slug); out = {}
    for k, (cls, prop, metr) in TOP.items():
        vals = " ".join("wd:" + c for c in cls.split())
        rows = []
        if prop:  # erst mit Kennzahl versuchen
            q = f"""SELECT ?item ?itemLabel ?coord ?v ?d WHERE {{ {f} VALUES ?c {{ {vals} }} ?item wdt:P31 ?c; p:{prop} ?st. ?st ps:{prop} ?v.
  OPTIONAL {{ ?st pq:P585 ?d. }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }} }} LIMIT 3000"""
            b = sparql(q) or []
            best = {}
            for r in b:
                qid = r["item"]["value"].rsplit("/", 1)[1]
                try:
                    v = float(r["v"]["value"])
                except (KeyError, ValueError):
                    continue
                d = r.get("d", {}).get("value", "")[:4]
                old = best.get(qid)
                if old is None or (d, v) > (old[4], old[3]):
                    c = r["coord"]["value"]; lon, lat = map(float, c[c.index("(") + 1:c.index(")")].split())
                    best[qid] = [r.get("itemLabel", {}).get("value", qid), round(lat, 5), round(lon, 5), v, d, qid]
            rows = sorted((x for x in best.values() if x[0] != x[5]), key=lambda x: -x[3])[:10]
            if len(rows) < 8:  # zu wenige Zahlen – dann lieber ehrlich nach Bekanntheit
                rows = []
        if not rows:  # sonst nach Bekanntheit
            metr = "sitelinks"
            q = f"""SELECT ?item ?itemLabel ?coord (MAX(?s) AS ?sl) WHERE {{ {f} VALUES ?c {{ {vals} }} ?item wdt:P31 ?c; wikibase:sitelinks ?s.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }} }} GROUP BY ?item ?itemLabel ?coord ORDER BY DESC(?sl) LIMIT 25"""
            seen = set()
            for r in sparql(q) or []:
                qid = r["item"]["value"].rsplit("/", 1)[1]; name = r.get("itemLabel", {}).get("value", qid)
                if qid in seen or name == qid:
                    continue
                seen.add(qid); c = r["coord"]["value"]; lon, lat = map(float, c[c.index("(") + 1:c.index(")")].split())
                rows.append([name, round(lat, 5), round(lon, 5), int(r["sl"]["value"]), "", qid])
                if len(rows) == 10:
                    break
        if len(rows) >= 3:  # weniger als 3 Einträge: Liste weglassen
            out[k] = {"m": metr, "L": rows}
        print(f"  Top 10 {k}: {len(rows)} ({metr})"); time.sleep(4)
    return out


# ---------------- Top 10 Restaurants: Michelin-Sterne (Wikidata), dann Wikipedia-Aufrufe der letzten 30 Tage ----------------
def aufrufe(wiki, titel):
    """Summe der Seitenaufrufe (Menschen, alle Geräte) der letzten 30 Tage – Wikimedia-Pageviews-API."""
    bis = datetime.date.today() - datetime.timedelta(days=1); von = bis - datetime.timedelta(days=29)
    t = urllib.parse.quote(titel.replace(" ", "_"), safe="")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{wiki}/all-access/user/{t}/daily/{von:%Y%m%d}00/{bis:%Y%m%d}00"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
            return sum(i["views"] for i in json.load(r).get("items", []))
    except Exception:
        return 0


def sterne(label):
    l = label.lower()
    if "green" in l or "bib" in l or "guide" in l:
        return 0
    for n, w in ((3, ("3", "three", "drei")), (2, ("2", "two", "zwei")), (1, ("1", "one", "ein"))):
        if any(x in l for x in w):
            return n
    return 1


def top_restaurants(sp, sprachen, slug):
    f = ort_filter(sp, slug); lang = ",".join(dict.fromkeys(sprachen + ["de", "en"]))
    q = f"""SELECT ?item ?itemLabel ?coord ?awl ?art WHERE {{ {f} ?item wdt:P31/wdt:P279? wd:Q11707 .
  OPTIONAL {{ ?item wdt:P166 ?aw . ?aw rdfs:label ?awl . FILTER(LANG(?awl)="en" && CONTAINS(LCASE(?awl), "michelin")) }}
  OPTIONAL {{ ?art schema:about ?item ; schema:isPartOf ?w . FILTER(?w IN (<https://{sprachen[0]}.wikipedia.org/>, <https://de.wikipedia.org/>, <https://en.wikipedia.org/>)) }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }} }} LIMIT 4000"""
    it = {}
    for r in sparql(q) or []:
        qid = r["item"]["value"].rsplit("/", 1)[1]; name = r.get("itemLabel", {}).get("value", qid)
        if name == qid:
            continue
        c = r["coord"]["value"]; lon, lat = map(float, c[c.index("(") + 1:c.index(")")].split())
        e = it.setdefault(qid, {"n": name, "lat": round(lat, 5), "lon": round(lon, 5), "st": 0, "art": set()})
        if "awl" in r:
            e["st"] = max(e["st"], sterne(r["awl"]["value"]))
        if "art" in r:
            e["art"].add(r["art"]["value"])
    kand = [e for e in it.values() if e["st"] or e["art"]]
    print(f"  Top 10 rest: {len(it)} Restaurants in Wikidata, {sum(1 for e in kand if e['st'])} mit Michelin-Stern, {len(kand)} Kandidaten")
    kand.sort(key=lambda e: -e["st"]); kand = kand[:60]
    for e in kand:
        v = 0
        for a in e["art"]:
            host, titel = a.split("//", 1)[1].split("/wiki/", 1)
            v = max(v, aufrufe(host, urllib.parse.unquote(titel)))
        e["v"] = v; time.sleep(0.2)
    kand.sort(key=lambda e: (-e["st"], -e["v"]))
    return [[e["n"], e["lat"], e["lon"], e["v"], "⭐" * e["st"], qid] for qid, e in
            ((next(k for k, x in it.items() if x is e), e) for e in kand[:10])]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    neu = "--neu" in sys.argv
    cfg = json.loads((ROOT / "portale.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for p in cfg["portale"]:
        sp = p.get("spiel")
        if not sp or not sp.get("bbox") or (args and p["slug"] not in args):
            continue
        f = OUT / f"{p['repo']}.json"
        if f.exists() and not neu:
            alt = json.loads(f.read_text(encoding="utf-8")).get("stand", "2000-01-01")
            if (datetime.date.today() - datetime.date.fromisoformat(alt)).days < 7:
                print(f"{p['slug']}: aktuell (Stand {alt})"); continue
        print(f"{p['slug']}: hole Orte …")
        try:
            if sp.get("stadt"):
                erg = stadt(sp)
            else:
                erg = land(sp, list((sp.get("titel") or {}).keys())[:2])
        except Exception as e:
            print(f"{p['slug']}: Fehler – {e}"); erg = None
        if not erg and f.exists():
            erg = json.loads(f.read_text(encoding="utf-8")).get("c")
            print(f"{p['slug']}: Orte unverändert aus alter Datei, nur Top 10 neu")
        if not erg:
            print(f"{p['slug']}: keine Daten – alte Datei bleibt"); continue
        try:
            spr = list((sp.get("titel") or {}).keys())[:2] or ["de"]
            top = top10(sp, spr, p["slug"])
            try:
                rr = top_restaurants(sp, spr, p["slug"])
                if len(rr) >= 3:
                    top["rest"] = {"m": "michelin", "L": rr}
            except Exception as e:
                print("  Top 10 Restaurants Fehler:", e)
            for k, v in top.items():
                print(f"  Top 10 {k} ({v['m']}): " + "; ".join(f"{i+1}. {r[0]}" for i, r in enumerate(v["L"][:10])))
        except Exception as e:
            print(f"{p['slug']}: Top 10 Fehler – {e}"); top = {}
        f.write_text(json.dumps({"stand": datetime.date.today().isoformat(), "stadt": bool(sp.get("stadt")),
                                 "quelle": "osm" if sp.get("stadt") else "wikidata", "c": erg, "top": top},
                                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{p['slug']}: " + ", ".join(f"{k} {len(v)}" for k, v in erg.items()) + f" – {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
