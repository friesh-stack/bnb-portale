#!/usr/bin/env python3
"""Erzeugt alle Gästeportale aus portale.json nach dist/<repo>/.

Aufruf:  python scripts/build.py            (alle Portale)
         python scripts/build.py sylt hamburg (nur diese Slugs)

Liest:   portale.json, content/<slug>.json (News), photos/<slug>.json (+ Bilder)
Schreibt: dist/<repo>/index.html (nur modus "neu"), aktuell.html, impressum.html,
          datenschutz.html, CNAME, assets/, fotos/
"""
import datetime as dt
import html
import json
import shutil
import sys
from pathlib import Path

import config

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
HEUTE = dt.date.today()

UI = {
    "de": {"aktuell": "Aktuell", "karte": "Karte", "entdecken": "Entdecken", "unterkuenfte": "Unterkünfte",
           "gastgeber": "Für Gastgeber", "news_titel": "Was ist los {ri}?", "news_leer": "Die ersten Meldungen erscheinen hier in Kürze.",
           "stand": "Stand", "quelle": "Quelle", "karte_titel": "{r} auf der Karte", "karte_laden": "Karte laden",
           "karte_hinweis": "Die Karte wird von OpenStreetMap geladen. Dabei wird Ihre IP-Adresse an die OpenStreetMap Foundation übertragen.",
           "beispiel": "Beispielhafte Hinweise – werden laufend ergänzt.", "entdecken_titel": "Das erwartet Sie",
           "unterk_titel": "Unterkünfte direkt vom Gastgeber", "unterk_frei": "Hier kann Ihre Ferienwohnung stehen",
           "unterk_frei_text": "Eigene Unterseite mit Fotos, Preisen und Anfrage direkt an Sie.", "mehr": "Mehr erfahren",
           "g_titel": "Sie vermieten {ri}?", "g_text": "Gäste suchen hier nach Unterkünften. Wir erstellen Ihnen mit KI eine eigene Unterseite – Sie erzählen, laden Fotos hoch, fertig.",
           "g_cta": "Unterkunft eintragen", "impressum": "Impressum", "datenschutz": "Datenschutz", "fotos": "Fotos",
           "projekt": "Ein friesh-stack Projekt", "schwester": "Weitere Portale", "burano": "Auch in Italien: Burano",
           "start": "Startseite", "zur_karte": "Zur Karte", "hero_cta": "Was ist los?", "geschlossen": "Ende"},
    "en": {"aktuell": "What's on", "karte": "Map", "entdecken": "Discover", "unterkuenfte": "Stays",
           "gastgeber": "For hosts", "news_titel": "What's on {ri}?", "news_leer": "The first updates will appear here soon.",
           "stand": "Updated", "quelle": "Source", "karte_titel": "{r} on the map", "karte_laden": "Load map",
           "karte_hinweis": "The map is loaded from OpenStreetMap, which transfers your IP address to the OpenStreetMap Foundation.",
           "beispiel": "Example pointers – more are added over time.", "entdecken_titel": "What awaits you",
           "unterk_titel": "Stays direct from the host", "unterk_frei": "Your holiday home could be here",
           "unterk_frei_text": "Your own page with photos, prices and enquiries straight to you.", "mehr": "Learn more",
           "g_titel": "Do you rent out {ri}?", "g_text": "Guests look for places to stay here. We build your own page with AI – you tell us about it, upload photos, done.",
           "g_cta": "List your property", "impressum": "Legal notice", "datenschutz": "Privacy", "fotos": "Photos",
           "projekt": "A friesh-stack project", "schwester": "More portals", "burano": "Also in Italy: Burano",
           "start": "Home", "zur_karte": "To the map", "hero_cta": "What's on?", "geschlossen": "Until"},
    "it": {"aktuell": "Novità", "karte": "Mappa", "entdecken": "Scoprire", "unterkuenfte": "Alloggi",
           "gastgeber": "Per gli host", "news_titel": "Cosa succede {ri}?", "news_leer": "Le prime notizie appariranno qui a breve.",
           "stand": "Aggiornato", "quelle": "Fonte", "karte_titel": "{r} sulla mappa", "karte_laden": "Carica mappa",
           "karte_hinweis": "La mappa viene caricata da OpenStreetMap; il vostro indirizzo IP viene trasmesso alla OpenStreetMap Foundation.",
           "beispiel": "Indicazioni di esempio – in continuo aggiornamento.", "entdecken_titel": "Cosa vi aspetta",
           "unterk_titel": "Alloggi direttamente dall'host", "unterk_frei": "Qui può comparire la vostra casa vacanze",
           "unterk_frei_text": "Una pagina propria con foto, prezzi e richieste direttamente a voi.", "mehr": "Scopri di più",
           "g_titel": "Affittate {ri}?", "g_text": "Qui gli ospiti cercano alloggio. Creiamo con l'IA la vostra pagina – raccontate, caricate le foto, fatto.",
           "g_cta": "Inserire l'alloggio", "impressum": "Note legali", "datenschutz": "Privacy", "fotos": "Foto",
           "projekt": "Un progetto friesh-stack", "schwester": "Altri portali", "burano": "Anche a Burano",
           "start": "Home", "zur_karte": "Alla mappa", "hero_cta": "Cosa succede?", "geschlossen": "Fino al"},
    "fr": {"aktuell": "Actualités", "karte": "Carte", "entdecken": "Découvrir", "unterkuenfte": "Logements",
           "gastgeber": "Pour les hôtes", "news_titel": "Que se passe-t-il {ri} ?", "news_leer": "Les premières actualités apparaîtront ici bientôt.",
           "stand": "Mis à jour", "quelle": "Source", "karte_titel": "{r} sur la carte", "karte_laden": "Charger la carte",
           "karte_hinweis": "La carte est chargée depuis OpenStreetMap ; votre adresse IP est transmise à l'OpenStreetMap Foundation.",
           "beispiel": "Repères d'exemple – complétés au fil du temps.", "entdecken_titel": "Ce qui vous attend",
           "unterk_titel": "Logements directement chez l'hôte", "unterk_frei": "Votre location pourrait être ici",
           "unterk_frei_text": "Votre propre page avec photos, prix et demandes directement chez vous.", "mehr": "En savoir plus",
           "g_titel": "Vous louez {ri} ?", "g_text": "Les voyageurs cherchent ici un logement. Nous créons votre page avec l'IA – vous racontez, ajoutez des photos, c'est prêt.",
           "g_cta": "Inscrire mon logement", "impressum": "Mentions légales", "datenschutz": "Confidentialité", "fotos": "Photos",
           "projekt": "Un projet friesh-stack", "schwester": "Autres portails", "burano": "Aussi en Italie : Burano",
           "start": "Accueil", "zur_karte": "Vers la carte", "hero_cta": "Quoi de neuf ?", "geschlossen": "Jusqu'au"},
    "es": {"aktuell": "Novedades", "karte": "Mapa", "entdecken": "Descubrir", "unterkuenfte": "Alojamientos",
           "gastgeber": "Para anfitriones", "news_titel": "¿Qué pasa {ri}?", "news_leer": "Las primeras novedades aparecerán aquí pronto.",
           "stand": "Actualizado", "quelle": "Fuente", "karte_titel": "{r} en el mapa", "karte_laden": "Cargar mapa",
           "karte_hinweis": "El mapa se carga desde OpenStreetMap; su dirección IP se transmite a la OpenStreetMap Foundation.",
           "beispiel": "Indicaciones de ejemplo – se amplían con el tiempo.", "entdecken_titel": "Lo que le espera",
           "unterk_titel": "Alojamientos directamente del anfitrión", "unterk_frei": "Aquí puede aparecer su alojamiento",
           "unterk_frei_text": "Su propia página con fotos, precios y consultas directas.", "mehr": "Más información",
           "g_titel": "¿Alquila {ri}?", "g_text": "Aquí los viajeros buscan alojamiento. Creamos su página con IA – usted cuenta, sube fotos y listo.",
           "g_cta": "Publicar mi alojamiento", "impressum": "Aviso legal", "datenschutz": "Privacidad", "fotos": "Fotos",
           "projekt": "Un proyecto friesh-stack", "schwester": "Más portales", "burano": "También en Italia: Burano",
           "start": "Inicio", "zur_karte": "Al mapa", "hero_cta": "¿Qué pasa?", "geschlossen": "Hasta"},
    "nl": {"aktuell": "Actueel", "karte": "Kaart", "entdecken": "Ontdekken", "unterkuenfte": "Accommodaties",
           "gastgeber": "Voor verhuurders", "news_titel": "Wat is er te doen {ri}?", "news_leer": "De eerste berichten verschijnen hier binnenkort.",
           "stand": "Bijgewerkt", "quelle": "Bron", "karte_titel": "{r} op de kaart", "karte_laden": "Kaart laden",
           "karte_hinweis": "De kaart wordt geladen van OpenStreetMap; daarbij wordt uw IP-adres doorgegeven aan de OpenStreetMap Foundation.",
           "beispiel": "Voorbeeldmarkeringen – worden steeds aangevuld.", "entdecken_titel": "Wat u te wachten staat",
           "unterk_titel": "Accommodaties direct van de verhuurder", "unterk_frei": "Hier kan uw vakantiewoning staan",
           "unterk_frei_text": "Een eigen pagina met foto's, prijzen en aanvragen rechtstreeks naar u.", "mehr": "Meer informatie",
           "g_titel": "Verhuurt u {ri}?", "g_text": "Gasten zoeken hier een verblijf. Wij maken met AI uw eigen pagina – u vertelt, uploadt foto's, klaar.",
           "g_cta": "Accommodatie aanmelden", "impressum": "Colofon", "datenschutz": "Privacy", "fotos": "Foto's",
           "projekt": "Een friesh-stack project", "schwester": "Meer portalen", "burano": "Ook in Italië: Burano",
           "start": "Home", "zur_karte": "Naar de kaart", "hero_cta": "Wat is er te doen?", "geschlossen": "Tot"},
}
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
PRAEP = {"de": "in", "en": "in", "it": "in", "fr": "en", "es": "en", "nl": "in"}
SPRACHNAME = {"de": "DE", "en": "EN", "it": "IT", "fr": "FR", "es": "ES", "nl": "NL"}

E = lambda s: html.escape(str(s), quote=True)


def lade_json(pfad, standard):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return standard


class Seite:
    def __init__(self, cfg, p, alle):
        self.cfg, self.p, self.alle = cfg, p, alle
        self.sp = p["sprachen"]
        # Vermieter-Bereich: eigene Sprachreihenfolge (z. B. Landessprache, Englisch, Deutsch);
        # wählt der Gast eine andere Sprache, sieht er diesen Bereich auf Englisch
        self.vsp = p.get("sprachen_vermieter", self.sp)

    def eff(self, s, vermieter):
        if not vermieter or s in self.vsp:
            return s
        return "en" if "en" in self.vsp else self.vsp[0]

    def wert(self, obj, sprache):
        if isinstance(obj, str):
            return obj
        return obj.get(sprache) or obj.get("de") or obj.get("en") or next(iter(obj.values()), "")

    def t(self, obj, tag="span", fmt=None, vermieter=False):
        """Mehrsprachiger Text: je Sprache ein Element, nur die erste ist sichtbar."""
        if isinstance(obj, str) and fmt is None:
            return E(obj)
        teile = []
        for i, s in enumerate(self.sp):
            txt = self.wert(obj, self.eff(s, vermieter)) if not isinstance(obj, str) else obj
            if fmt:
                txt = fmt(s, txt)
            teile.append(f'<{tag} lang="{s}"{"" if i == 0 else " hidden"}>{E(txt)}</{tag}>')
        return "".join(teile)

    def region_in(self, s):
        ri = self.p.get("region_in", {})
        return ri.get(s) or f'{PRAEP[s]} {self.wert(self.p["region"], s)}'

    def ui(self, key, vermieter=False, **kw):
        out = []
        for i, s in enumerate(self.sp):
            v = self.eff(s, vermieter)
            txt = UI[v][key].format(r=self.wert(self.p["region"], v), ri=self.region_in(v), **kw)
            out.append(f'<span lang="{s}"{"" if i == 0 else " hidden"}>{E(txt)}</span>')
        return "".join(out)

    # ---------- Bausteine ----------
    def kopf(self, titel_txt, beschreibung, aktiv="index"):
        p = self.p
        langs = "".join(f'<button type="button" data-lang="{s}">{SPRACHNAME[s]}</button>' for s in self.sp) if len(self.sp) > 1 else ""
        start = "index.html" if p["modus"] == "neu" else "./"
        nav = (f'<a href="{start}#aktuell">{self.ui("aktuell")}</a><a href="{start}#karte">{self.ui("karte")}</a>'
               if aktiv != "aktuell" else f'<a href="#aktuell">{self.ui("aktuell")}</a><a href="#karte">{self.ui("karte")}</a>')
        if p["modus"] == "neu" and aktiv == "index":
            nav += f'<a href="#entdecken">{self.ui("entdecken")}</a><a href="#unterkuenfte">{self.ui("unterkuenfte")}</a>'
        nav += f'<a class="nav-cta" href="{"#gastgeber" if aktiv != "recht" else start + "#gastgeber"}">{self.ui("gastgeber", vermieter=True)}</a>'
        return f"""<!DOCTYPE html>
<html lang="{self.sp[0]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(titel_txt)}</title>
<meta name="description" content="{E(beschreibung)}">
<link rel="canonical" href="https://{p['domain']}/">
<meta property="og:title" content="{E(titel_txt)}">
<meta property="og:description" content="{E(beschreibung)}">
<meta name="theme-color" content="#1d4f73">
<link rel="stylesheet" href="assets/portal.css">
</head>
<body>
<header class="kopf">
  <a class="logo" href="{start}">{E(p['marke'])}</a>
  <nav>{nav}</nav>
  <div class="langs">{langs}</div>
</header>
"""

    def news_block(self):
        daten = lade_json(ROOT / "content" / f"{self.p['slug']}.json", {"items": []})
        items = [i for i in daten.get("items", []) if not i.get("bis") or i["bis"] >= HEUTE.isoformat()][:6]
        karten = []
        for i in items:
            datum = i.get("datum", "")
            try:
                datum_txt = dt.date.fromisoformat(datum).strftime("%d.%m.%Y")
            except ValueError:
                datum_txt = datum
            quelle = (f'<a class="quelle" href="{E(i["quelle"])}" target="_blank" rel="noopener">{self.ui("quelle")}: {E(i.get("quelle_name", ""))}</a>'
                      if i.get("quelle") else "")
            karten.append(f'<article class="news"><time>{E(datum_txt)}</time><h3>{self.t(i["titel"])}</h3>'
                          f'<p>{self.t(i["text"])}</p>{quelle}</article>')
        inhalt = "".join(karten) or f'<p class="leer">{self.ui("news_leer")}</p>'
        stand = f'<p class="stand">{self.ui("stand")}: {E(daten.get("stand", ""))}</p>' if daten.get("stand") else ""
        return f"""<section id="aktuell" class="block">
  <h2>{self.ui("news_titel")}</h2>
<!-- AUTO:news:start -->
  <div class="news-grid">{inhalt}</div>
  {stand}
<!-- AUTO:news:end -->
</section>
"""

    def karte_block(self):
        p = self.p
        pfeile = []
        for m in p.get("pfeile", []):
            pfeile.append({"n": m["name"], "lat": m["lat"], "lon": m["lon"], "link": m.get("link", ""),
                           "t": {s: self.wert(m.get("text", ""), s) for s in self.sp}})
        daten = json.dumps({"c": [p["karte"]["lat"], p["karte"]["lon"]], "z": p["karte"]["zoom"], "p": pfeile}, ensure_ascii=False)
        return f"""<section id="karte" class="block">
  <h2>{self.ui("karte_titel")}</h2>
  <div id="map" class="map">
    <div class="map-consent">
      <p>{self.ui("karte_hinweis")}</p>
      <button type="button" id="mapLaden" class="btn">{self.ui("karte_laden")}</button>
    </div>
  </div>
  <p class="hinweis">{self.ui("beispiel")}</p>
  <script type="application/json" id="mapDaten">{daten.replace("</", "<\\/")}</script>
</section>
"""

    def gastgeber_block(self):
        ang = self.cfg["angebote"][self.p["angebot"]]
        return f"""<section id="gastgeber" class="gastgeber">
  <div class="block">
    <h2>{self.ui("g_titel", vermieter=True)}</h2>
    <p>{self.ui("g_text", vermieter=True)}</p>
    <p class="preis">{self.t(ang["preis"], vermieter=True)}</p>
    <a class="btn btn-hell" href="{E(ang["url"])}">{self.ui("g_cta", vermieter=True)}</a>
  </div>
</section>
"""

    def fuss(self, fotos):
        p = self.p
        andere = [x for x in self.alle if x["slug"] != p["slug"]]
        links = " · ".join(f'<a href="https://{E(x["domain"])}">{E(x["marke"])}</a>' for x in andere)
        credits = ""
        if fotos:
            credits = '<p class="credits">' + self.ui("fotos") + ": " + " · ".join(
                f'<a href="{E(f["seite"])}" target="_blank" rel="noopener">{E(f.get("autor") or "Wikimedia Commons")}</a>'
                f' (<a href="{E(f.get("lizenz_url") or f["seite"])}" target="_blank" rel="noopener">{E(f.get("lizenz", ""))}</a>)'
                for f in fotos) + "</p>"
        return f"""<footer class="fuss">
  <p><a href="impressum.html">{self.ui("impressum")}</a> · <a href="datenschutz.html">{self.ui("datenschutz")}</a></p>
  <p class="schwester"><strong>{self.ui("schwester")}:</strong> {links}</p>
  <p><a href="https://myburano.com">{self.ui("burano")}</a></p>
  {credits}
  <p class="sig">{self.ui("projekt")}</p>
</footer>
<script src="assets/portal.js"></script>
</body>
</html>
"""

    def fotos(self):
        return lade_json(ROOT / "photos" / f"{self.p['slug']}.json", [])

    # ---------- Seiten ----------
    def index(self):
        p = self.p
        fotos = self.fotos()
        s0 = self.sp[0]
        titel = self.wert(p["titel"], s0)
        intro0 = self.wert(p["intro"], s0)
        slides = "".join(f'<div class="slide{" an" if i == 0 else ""}" style="background-image:url(\'{E(f["datei"])}\')" role="img" aria-label="{E(f.get("titel", ""))}"></div>'
                         for i, f in enumerate(fotos[:6]))
        hl = []
        for i, h in enumerate(p.get("highlights", [])):
            bild = fotos[(i + 1) % len(fotos)]["datei"] if fotos else ""
            bildtag = f'<div class="hl-bild" style="background-image:url(\'{E(bild)}\')"></div>' if bild else '<div class="hl-bild leer"></div>'
            link = f' <a href="{E(h["link"])}">{self.ui("mehr")} →</a>' if h.get("link") else ""
            hl.append(f'<article class="hl">{bildtag}<div class="hl-text"><h3>{self.t(h["titel"])}</h3><p>{self.t(h["text"])}{link}</p></div></article>')
        ang_url = self.cfg["angebote"][p["angebot"]]["url"]
        frei = "".join(f'<a class="frei" href="{E(ang_url)}"><span class="plus">+</span><h3>{self.ui("unterk_frei", vermieter=True)}</h3><p>{self.ui("unterk_frei_text", vermieter=True)}</p></a>' for _ in range(3))
        return (self.kopf(f'{p["marke"]} – {titel}', intro0) + f"""<main>
<section class="hero">
  <div class="slides">{slides}</div>
  <div class="hero-inhalt">
    <h1>{self.t(p["titel"])}</h1>
    <p>{self.t(p["intro"])}</p>
    <div class="hero-btns"><a class="btn" href="#aktuell">{self.ui("hero_cta")}</a><a class="btn btn-rand" href="#karte">{self.ui("zur_karte")}</a></div>
  </div>
</section>
""" + self.news_block() + self.karte_block() + f"""<section id="entdecken" class="block">
  <h2>{self.ui("entdecken_titel")}</h2>
  <div class="hl-grid">{"".join(hl)}</div>
</section>
<section id="unterkuenfte" class="block">
  <h2>{self.ui("unterk_titel")}</h2>
  <div class="frei-grid">{frei}</div>
</section>
""" + self.gastgeber_block() + "</main>\n" + self.fuss(fotos))

    def aktuell(self):
        p = self.p
        s0 = self.sp[0]
        titel = f'{p["marke"]} – {UI[s0]["news_titel"].format(ri=self.region_in(s0))}'
        return (self.kopf(titel, titel, aktiv="aktuell") + "<main>\n" + self.news_block() + self.karte_block()
                + self.gastgeber_block() + "</main>\n" + self.fuss(self.fotos()))

    def impressum(self):
        b = self.cfg["betreiber"]
        marken = ", ".join(f'{x["marke"]} ({x["domain"]})' for x in self.alle)
        return self.kopf(f'Impressum – {self.p["marke"]}', "Impressum", aktiv="recht") + f"""<main class="block recht">
<h1>Impressum</h1>
<p lang="en" class="klein">Legal notice according to German law.</p>
<h2>Angaben gemäß § 5 DDG</h2>
<p>{E(b["name"])}<br>{E(b["strasse"])}<br>{E(b["ort"])}<br>{E(b["land"])}</p>
<h2>Kontakt</h2>
<p>E-Mail: <a href="mailto:{E(b["email"])}">{E(b["email"])}</a></p>
<p>{E(marken)} sind Angebote von {E(b["name"])}.</p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>{E(b["name"])}, Anschrift wie oben</p>
<h2>Verbraucherstreitbeilegung</h2>
<p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
<h2>Inserate und Meldungen</h2>
<p>Für die Inhalte der einzelnen Inserate sind die jeweiligen Vermieterinnen und Vermieter verantwortlich. Mietverträge kommen ausschließlich zwischen Gast und Vermieter zustande. Die Meldungen unter „Aktuell“ werden mit KI-Unterstützung aus öffentlichen Quellen zusammengefasst; die jeweilige Quelle ist verlinkt.</p>
</main>
""" + self.fuss(self.fotos())

    def datenschutz(self):
        b = self.cfg["betreiber"]
        return self.kopf(f'Datenschutz – {self.p["marke"]}', "Datenschutzerklärung", aktiv="recht") + f"""<main class="block recht">
<h1>Datenschutzerklärung</h1>
<p class="klein">Stand: {MONATE[HEUTE.month - 1]} {HEUTE.year}</p>
<h2>1. Verantwortlicher</h2>
<p>{E(b["name"])}, {E(b["strasse"])}, {E(b["ort"])}, E-Mail: {E(b["email"])}</p>
<h2>2. Das Wichtigste in Kürze</h2>
<p>Diese Website setzt keine Cookies, kein Tracking und keine Analyse-Werkzeuge ein. Schriften, Kartenbibliothek und Fotos werden von unserem eigenen Webspace geladen. Nur wenn Sie die Karte ausdrücklich laden, werden Kartenkacheln von OpenStreetMap abgerufen.</p>
<h2>3. Hosting und Server-Logfiles</h2>
<p>Die Website wird über GitHub Pages bereitgestellt (GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). Beim Aufruf verarbeitet GitHub technisch notwendige Daten wie IP-Adresse, Zeitpunkt und aufgerufene Seite, um die Seite auszuliefern und die Sicherheit zu gewährleisten (Art. 6 Abs. 1 lit. f DSGVO).</p>
<h2>4. Karte (OpenStreetMap)</h2>
<p>Die Karte wird erst nach Klick auf „Karte laden“ angezeigt. Dann werden Kartenkacheln von Servern der OpenStreetMap Foundation (St John’s Innovation Centre, Cowley Road, Cambridge, CB4 0WS, Vereinigtes Königreich) geladen; dabei wird Ihre IP-Adresse übertragen (Art. 6 Abs. 1 lit. a DSGVO – Ihre Einwilligung durch den Klick).</p>
<h2>5. Fotos</h2>
<p>Die Fotos stammen von Wikimedia Commons und werden unter den jeweils angegebenen freien Lizenzen genutzt. Sie liegen auf unserem eigenen Webspace; beim Anzeigen werden keine Daten an Wikimedia übertragen.</p>
<h2>6. Kontakt per E-Mail</h2>
<p>Wenn Sie uns schreiben, verarbeiten wir Ihre Angaben zur Bearbeitung Ihrer Anfrage (Art. 6 Abs. 1 lit. b DSGVO) und löschen sie, wenn sie nicht mehr benötigt werden.</p>
<h2>7. Übermittlung in Drittländer</h2>
<p>Für GitHub (USA) erfolgt die Übermittlung auf Grundlage des EU-US Data Privacy Framework bzw. von Standardvertragsklauseln. Für das Vereinigte Königreich besteht ein Angemessenheitsbeschluss der EU-Kommission.</p>
<h2>8. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie auf Beschwerde bei einer Datenschutz-Aufsichtsbehörde.</p>
</main>
""" + self.fuss(self.fotos())


def baue(cfg, p, alle):
    ziel = DIST / p["repo"]
    if ziel.exists():
        shutil.rmtree(ziel)
    (ziel / "assets").mkdir(parents=True)
    for unter in ("fonts", "leaflet"):
        shutil.copytree(ROOT / "assets" / unter, ziel / "assets" / unter)
    for datei in ("portal.css", "portal.js"):
        shutil.copy(ROOT / "assets" / datei, ziel / "assets" / datei)
    fotos_dir = ROOT / "photos" / p["slug"]
    if fotos_dir.is_dir():
        shutil.copytree(fotos_dir, ziel / "fotos" / p["slug"])
    s = Seite(cfg, p, alle)
    if p["modus"] == "neu":
        (ziel / "index.html").write_text(s.index(), encoding="utf-8")
        if p.get("allinkl") == "dns":  # bei Weiterleitung KEIN CNAME, sonst Endlosschleife
            (ziel / "CNAME").write_text(p["domain"] + "\n", encoding="utf-8")
        (ziel / ".nojekyll").write_text("", encoding="utf-8")
    (ziel / "aktuell.html").write_text(s.aktuell(), encoding="utf-8")
    (ziel / "impressum.html").write_text(s.impressum(), encoding="utf-8")
    (ziel / "datenschutz.html").write_text(s.datenschutz(), encoding="utf-8")
    return ziel


def baue_umleitung(p):
    """Mini-Seite für eine Zusatz-Domain: leitet sofort (mit Pfad) auf die Hauptdomain weiter."""
    ziel = DIST / p["repo"]
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    url = f"https://{p['ziel']}/"
    seite = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{E(p['marke'])}</title>
<link rel="canonical" href="{url}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace("{url}" + location.pathname.replace(/^\\//, "") + location.search + location.hash);</script>
</head><body><p>Weiter zu <a href="{url}">{E(p['ziel'])}</a></p></body></html>
"""
    for name in ("index.html", "404.html"):
        (ziel / name).write_text(seite, encoding="utf-8")
    (ziel / "CNAME").write_text(p["domain"] + "\n", encoding="utf-8")
    (ziel / ".nojekyll").write_text("", encoding="utf-8")
    return ziel


def main(argv):
    cfg = config.lade(mit_umleitungen=True)
    alle = [p for p in cfg["portale"] if not p.get("umleitung")]
    auswahl = [p for p in cfg["portale"] if not argv or p["slug"].split("~")[0] in argv]
    for p in auswahl:
        ziel = baue_umleitung(p) if p.get("umleitung") else baue(cfg, p, alle)
        print(f"✓ {p['slug']:12} → {ziel.relative_to(ROOT)}  ({p['modus']})")


if __name__ == "__main__":
    main(sys.argv[1:])
