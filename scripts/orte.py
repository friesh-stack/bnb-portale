"""Wöchentlich: Orte für die Strategiespiele aus OpenStreetMap (Overpass) holen.
Schreibt content/orte/<repo>.json; build.py kopiert die Datei als orte.json ins Portal.
Aufruf: python scripts/orte.py [--neu] [slug ...]"""
import json, sys, time, urllib.request, urllib.parse, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "orte"
EP = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
UA = "friesh-stack-portale/1.0 (+https://github.com/friesh-stack)"

# Stadt-Spiele: alles. Länder-Spiele: nur bekannte Orte (mit Wikidata-Eintrag), Details lädt das Spiel beim Heranzoomen live.
CAT_STADT = {
    "sight": 'nwr["tourism"="attraction"]["name"];nwr["historic"~"^(castle|monument|ruins|city_gate|fort)$"]["name"];',
    "museum": 'nwr["tourism"~"^(museum|gallery)$"]["name"];',
    "rail": 'nwr["railway"~"^(station|halt)$"]["name"];',
    "bus": 'node["highway"="bus_stop"]["name"];',
    "shop": 'nwr["shop"~"^(mall|department_store|supermarket)$"];way["highway"="pedestrian"]["name"];',
    "fun": 'nwr["tourism"~"^(theme_park|zoo|aquarium)$"];nwr["leisure"="water_park"];',
    "stadium": 'nwr["leisure"="stadium"]["name"];',
    "garden": 'nwr["leisure"="garden"]["garden:type"="botanical"];nwr["leisure"="park"]["name"];',
    "view": 'nwr["tourism"="viewpoint"];nwr["man_made"="tower"]["tower:type"="observation"];',
    "theatre": 'nwr["amenity"~"^(theatre|arts_centre)$"]["name"];',
}
CAT_LAND = {
    "sight": 'nwr["tourism"="attraction"]["wikidata"];nwr["historic"~"^(castle|monument|ruins|city_gate|fort)$"]["wikidata"];',
    "museum": 'nwr["tourism"="museum"]["wikidata"];',
    "rail": 'nwr["railway"="station"]["wikidata"]["train"="yes"];',
    "shop": 'nwr["shop"~"^(mall|department_store)$"]["wikidata"];',
    "fun": 'nwr["tourism"~"^(theme_park|zoo|aquarium)$"]["wikidata"];',
    "stadium": 'nwr["leisure"="stadium"]["wikidata"];',
    "garden": 'nwr["leisure"="garden"]["garden:type"="botanical"]["name"];nwr["leisure"="park"]["wikidata"];',
    "view": 'nwr["man_made"="tower"]["tower:type"="observation"]["wikidata"];nwr["tourism"="viewpoint"]["wikidata"];',
    "theatre": 'nwr["amenity"="theatre"]["wikidata"];',
}
GRENZE = {"bus": 6000, "shop": 6000, "garden": 4000}  # höchstens so viele je Kategorie
KEEP = ("website", "contact:website", "opening_hours", "addr:street", "addr:housenumber", "addr:city")


def frage(q):
    data = urllib.parse.urlencode({"data": q}).encode()
    for ep in EP:
        for versuch in range(2):
            t0 = time.time()
            try:
                req = urllib.request.Request(ep, data=data, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=150) as r:
                    j = json.load(r)
                print(f"    {ep.split('/')[2]}: {len(j.get('elements', []))} Treffer in {time.time() - t0:.1f}s")
                return j
            except Exception as e:
                print(f"    {ep.split('/')[2]}: Fehler nach {time.time() - t0:.1f}s – {e}")
                time.sleep(10)
    return None


def hole(repo, bbox, stadt, iso=None):
    S, W, N, E = bbox
    erg = {}
    for k, filt in (CAT_STADT if stadt else CAT_LAND).items():
        if iso:  # Länder: nur Orte innerhalb der Landesgrenze
            teile = [t + "(area.a)" for t in filt.strip(";").split(";")]
            q = f'[out:json][timeout:120];area["ISO3166-1"="{iso}"][admin_level=2]->.a;(' + ";".join(teile) + ";);out tags center;"
        else:
            q = f"[out:json][timeout:120][bbox:{S},{W},{N},{E}];(" + filt + ");out tags center;"
        print(f"  {repo} · {k}")
        j = frage(q)
        if j is None:
            return None
        L = []
        for e in j.get("elements", []):
            c = e.get("center") or {}
            lat, lon = e.get("lat", c.get("lat")), e.get("lon", c.get("lon"))
            if lat is None:
                continue
            t = e.get("tags", {})
            row = [round(lat, 5), round(lon, 5), t.get("name", ""), e["type"][0] + str(e["id"])]
            ex = {x: t[x] for x in KEEP if x in t}
            if ex:
                row.append(ex)
            L.append(row)
        erg[k] = L[:GRENZE.get(k, 3000)]
        time.sleep(3)
    return erg


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
                print(f"{p['slug']}: aktuell (Stand {alt})")
                continue
        print(f"{p['slug']}: hole Orte …")
        erg = hole(p["repo"], sp["bbox"], sp.get("stadt", False), sp.get("iso"))
        if erg is None:
            print(f"{p['slug']}: Overpass nicht erreichbar – alte Datei bleibt")
            continue
        f.write_text(json.dumps({"stand": datetime.date.today().isoformat(), "stadt": sp.get("stadt", False), "c": erg},
                                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{p['slug']}: {sum(len(v) for v in erg.values())} Orte, {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
