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
from vermieter_texte import T as VT

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
    "da": {"aktuell": "Aktuelt", "karte": "Kort", "entdecken": "Opdag", "unterkuenfte": "Overnatning", "gastgeber": "For værter", "news_titel": "Hvad sker der {ri}?", "news_leer": "De første nyheder vises her snart.", "stand": "Opdateret", "quelle": "Kilde", "karte_titel": "{r} på kortet", "karte_laden": "Indlæs kort", "karte_hinweis": "Kortet indlæses fra OpenStreetMap; din IP-adresse sendes til OpenStreetMap Foundation.", "beispiel": "Eksempler på steder – udvides løbende.", "entdecken_titel": "Det venter dig", "unterk_titel": "Overnatning direkte fra værten", "unterk_frei": "Her kan dit feriehus stå", "unterk_frei_text": "Din egen side med billeder, priser og forespørgsler direkte til dig.", "mehr": "Læs mere", "g_titel": "Udlejer du {ri}?", "g_text": "Gæster leder efter overnatning her. Vi laver din egen side med AI – du fortæller, uploader billeder, færdig.", "g_cta": "Tilmeld din bolig", "impressum": "Kolofon", "datenschutz": "Privatliv", "fotos": "Fotos", "projekt": "Et friesh-stack-projekt", "schwester": "Flere portaler", "burano": "Også i Italien: Burano", "start": "Forside", "zur_karte": "Til kortet", "hero_cta": "Hvad sker der?", "geschlossen": "Indtil"},
    "sv": {"aktuell": "Aktuellt", "karte": "Karta", "entdecken": "Upptäck", "unterkuenfte": "Boende", "gastgeber": "För värdar", "news_titel": "Vad händer {ri}?", "news_leer": "De första nyheterna visas här snart.", "stand": "Uppdaterad", "quelle": "Källa", "karte_titel": "{r} på kartan", "karte_laden": "Ladda karta", "karte_hinweis": "Kartan laddas från OpenStreetMap; din IP-adress skickas till OpenStreetMap Foundation.", "beispiel": "Exempel på platser – fylls på löpande.", "entdecken_titel": "Det här väntar dig", "unterk_titel": "Boende direkt från värden", "unterk_frei": "Här kan ditt fritidshus synas", "unterk_frei_text": "Din egen sida med bilder, priser och förfrågningar direkt till dig.", "mehr": "Läs mer", "g_titel": "Hyr du ut {ri}?", "g_text": "Gäster söker boende här. Vi skapar din egen sida med AI – du berättar, laddar upp bilder, klart.", "g_cta": "Anmäl ditt boende", "impressum": "Juridisk information", "datenschutz": "Integritet", "fotos": "Foton", "projekt": "Ett friesh-stack-projekt", "schwester": "Fler portaler", "burano": "Även i Italien: Burano", "start": "Start", "zur_karte": "Till kartan", "hero_cta": "Vad händer?", "geschlossen": "Till och med"},
    "nb": {"aktuell": "Aktuelt", "karte": "Kart", "entdecken": "Oppdag", "unterkuenfte": "Overnatting", "gastgeber": "For utleiere", "news_titel": "Hva skjer {ri}?", "news_leer": "De første nyhetene vises her snart.", "stand": "Oppdatert", "quelle": "Kilde", "karte_titel": "{r} på kartet", "karte_laden": "Last inn kart", "karte_hinweis": "Kartet lastes fra OpenStreetMap; IP-adressen din sendes til OpenStreetMap Foundation.", "beispiel": "Eksempler på steder – utvides fortløpende.", "entdecken_titel": "Dette venter deg", "unterk_titel": "Overnatting direkte fra utleier", "unterk_frei": "Her kan feriehuset ditt stå", "unterk_frei_text": "Din egen side med bilder, priser og forespørsler direkte til deg.", "mehr": "Les mer", "g_titel": "Leier du ut {ri}?", "g_text": "Gjester leter etter overnatting her. Vi lager din egen side med KI – du forteller, laster opp bilder, ferdig.", "g_cta": "Registrer boligen din", "impressum": "Juridisk informasjon", "datenschutz": "Personvern", "fotos": "Bilder", "projekt": "Et friesh-stack-prosjekt", "schwester": "Flere portaler", "burano": "Også i Italia: Burano", "start": "Forside", "zur_karte": "Til kartet", "hero_cta": "Hva skjer?", "geschlossen": "Til og med"},
    "fi": {"aktuell": "Ajankohtaista", "karte": "Kartta", "entdecken": "Tutustu", "unterkuenfte": "Majoitus", "gastgeber": "Vuokranantajille", "news_titel": "Mitä tapahtuu {ri}?", "news_leer": "Ensimmäiset uutiset näkyvät täällä pian.", "stand": "Päivitetty", "quelle": "Lähde", "karte_titel": "{r} kartalla", "karte_laden": "Lataa kartta", "karte_hinweis": "Kartta ladataan OpenStreetMapista; IP-osoitteesi välitetään OpenStreetMap Foundationille.", "beispiel": "Esimerkkikohteita – lisää tulossa.", "entdecken_titel": "Tätä on luvassa", "unterk_titel": "Majoitus suoraan vuokranantajalta", "unterk_frei": "Tässä voisi olla lomakotisi", "unterk_frei_text": "Oma sivu kuvineen ja hintoineen, tiedustelut suoraan sinulle.", "mehr": "Lue lisää", "g_titel": "Vuokraatko {ri}?", "g_text": "Matkailijat etsivät täältä majoitusta. Teemme sinulle oman sivun tekoälyn avulla – kerrot, lataat kuvat, valmista.", "g_cta": "Ilmoita kohteesi", "impressum": "Oikeudelliset tiedot", "datenschutz": "Tietosuoja", "fotos": "Kuvat", "projekt": "friesh-stack-projekti", "schwester": "Lisää portaaleja", "burano": "Myös Italiassa: Burano", "start": "Etusivu", "zur_karte": "Kartalle", "hero_cta": "Mitä tapahtuu?", "geschlossen": "Asti"},
    "pt": {"aktuell": "Atualidades", "karte": "Mapa", "entdecken": "Descobrir", "unterkuenfte": "Alojamento", "gastgeber": "Para anfitriões", "news_titel": "O que se passa {ri}?", "news_leer": "As primeiras notícias aparecerão aqui em breve.", "stand": "Atualizado", "quelle": "Fonte", "karte_titel": "{r} no mapa", "karte_laden": "Carregar mapa", "karte_hinweis": "O mapa é carregado a partir do OpenStreetMap; o seu endereço IP é transmitido à OpenStreetMap Foundation.", "beispiel": "Pontos de exemplo – vão sendo ampliados.", "entdecken_titel": "O que o espera", "unterk_titel": "Alojamento diretamente do anfitrião", "unterk_frei": "Aqui pode estar o seu alojamento", "unterk_frei_text": "A sua própria página com fotos, preços e pedidos diretamente para si.", "mehr": "Saber mais", "g_titel": "Arrenda alojamento {ri}?", "g_text": "Os hóspedes procuram alojamento aqui. Criamos a sua página com IA – conta-nos, carrega as fotos, pronto.", "g_cta": "Registar alojamento", "impressum": "Ficha técnica", "datenschutz": "Privacidade", "fotos": "Fotos", "projekt": "Um projeto friesh-stack", "schwester": "Mais portais", "burano": "Também em Itália: Burano", "start": "Início", "zur_karte": "Ver mapa", "hero_cta": "O que há para fazer?", "geschlossen": "Até"},
    "hu": {"aktuell": "Aktuális", "karte": "Térkép", "entdecken": "Felfedezés", "unterkuenfte": "Szállások", "gastgeber": "Szállásadóknak", "news_titel": "Mi történik {ri}?", "news_leer": "Az első hírek hamarosan itt jelennek meg.", "stand": "Frissítve", "quelle": "Forrás", "karte_titel": "{r} a térképen", "karte_laden": "Térkép betöltése", "karte_hinweis": "A térkép az OpenStreetMapről töltődik be; IP-címét továbbítjuk az OpenStreetMap Foundation részére.", "beispiel": "Példahelyek – folyamatosan bővülnek.", "entdecken_titel": "Ami Önre vár", "unterk_titel": "Szállás közvetlenül a szállásadótól", "unterk_frei": "Itt lehetne az Ön szállása", "unterk_frei_text": "Saját oldal fotókkal, árakkal, a megkeresések közvetlenül Önhöz érkeznek.", "mehr": "Bővebben", "g_titel": "Szállást ad ki {ri}?", "g_text": "A vendégek itt keresnek szállást. Mesterséges intelligenciával elkészítjük saját oldalát – Ön elmeséli, feltölti a fotókat, kész.", "g_cta": "Szállás regisztrálása", "impressum": "Impresszum", "datenschutz": "Adatvédelem", "fotos": "Fotók", "projekt": "Egy friesh-stack projekt", "schwester": "További portálok", "burano": "Olaszországban is: Burano", "start": "Kezdőlap", "zur_karte": "A térképhez", "hero_cta": "Mi a program?", "geschlossen": "Eddig:"},
    "el": {"aktuell": "Επικαιρότητα", "karte": "Χάρτης", "entdecken": "Ανακαλύψτε", "unterkuenfte": "Καταλύματα", "gastgeber": "Για οικοδεσπότες", "news_titel": "Τι συμβαίνει {ri};", "news_leer": "Τα πρώτα νέα θα εμφανιστούν εδώ σύντομα.", "stand": "Ενημέρωση", "quelle": "Πηγή", "karte_titel": "{r} στον χάρτη", "karte_laden": "Φόρτωση χάρτη", "karte_hinweis": "Ο χάρτης φορτώνεται από το OpenStreetMap· η διεύθυνση IP σας διαβιβάζεται στο OpenStreetMap Foundation.", "beispiel": "Ενδεικτικά σημεία – συμπληρώνονται συνεχώς.", "entdecken_titel": "Τι σας περιμένει", "unterk_titel": "Καταλύματα απευθείας από τον οικοδεσπότη", "unterk_frei": "Εδώ μπορεί να εμφανίζεται το κατάλυμά σας", "unterk_frei_text": "Δική σας σελίδα με φωτογραφίες, τιμές και αιτήματα απευθείας σε εσάς.", "mehr": "Περισσότερα", "g_titel": "Νοικιάζετε κατάλυμα {ri};", "g_text": "Οι επισκέπτες αναζητούν εδώ κατάλυμα. Δημιουργούμε τη σελίδα σας με τεχνητή νοημοσύνη – μας λέτε, ανεβάζετε φωτογραφίες, έτοιμο.", "g_cta": "Καταχώριση καταλύματος", "impressum": "Στοιχεία εκδότη", "datenschutz": "Απόρρητο", "fotos": "Φωτογραφίες", "projekt": "Ένα έργο friesh-stack", "schwester": "Περισσότερες πύλες", "burano": "Και στην Ιταλία: Burano", "start": "Αρχική", "zur_karte": "Στον χάρτη", "hero_cta": "Τι γίνεται;", "geschlossen": "Έως"}
}
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
PRAEP = {"de": "in", "en": "in", "it": "in", "fr": "en", "es": "en", "nl": "in", "da": "i", "sv": "i", "nb": "i", "fi": "", "pt": "em", "hu": "", "el": "σε"}
SPRACHNAME = {"de": "DE", "en": "EN", "it": "IT", "fr": "FR", "es": "ES", "nl": "NL", "da": "DA", "sv": "SV", "nb": "NO", "fi": "FI", "pt": "PT", "hu": "HU", "el": "EL"}

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
        if len(self.sp) > 3:  # am Handy: Auswahlfeld statt vieler Knöpfe
            langs += '<select class="lang-select" aria-label="Sprache / Language">' + "".join(
                f'<option value="{s}">{SPRACHNAME[s]}</option>' for s in self.sp) + "</select>"
        start = "index.html" if p["modus"] == "neu" else "./"
        nav = (f'<a href="{start}#aktuell">{self.ui("aktuell")}</a><a href="{start}#karte">{self.ui("karte")}</a>'
               if aktiv != "aktuell" else f'<a href="#aktuell">{self.ui("aktuell")}</a><a href="#karte">{self.ui("karte")}</a>')
        if p["modus"] == "neu" and aktiv == "index":
            nav += f'<a href="#entdecken">{self.ui("entdecken")}</a><a href="#unterkuenfte">{self.ui("unterkuenfte")}</a>'
        if p.get("spiel"):  # Strategiespiel als eigene Seite (Datei liegt in extra/<repo>/)
            nav += f'<a href="{E(p["spiel"]["datei"])}">{self.t(p["spiel"]["nav"])}</a>'
        nav += f'<a class="nav-cta" href="{"#gastgeber" if aktiv != "recht" else start + "#gastgeber"}">{self.ui("gastgeber", vermieter=True)}</a>'
        return f"""<!DOCTYPE html>
<html lang="{self.sp[0]}" translate="no" class="notranslate">
<head>
<meta charset="utf-8">
<meta name="google" content="notranslate">
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
  <a class="logo" href="{start}">{logo_html(p['marke'])}</a>
  <nav>{nav}</nav>
  <div class="langs{" viele" if len(self.sp) > 3 else ""}">{langs}</div>
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

    def portal_url(self):
        """Link zum Vermietungsportal, bei eu-bnb.com/vermieten mit passender Sprache."""
        url = self.cfg["angebote"][self.p["angebot"]]["url"]
        return url + f"?lang={self.vsp[0]}" if "eu-bnb.com/vermieten" in url else url

    def gastgeber_block(self):
        ang = self.cfg["angebote"][self.p["angebot"]]
        return f"""<section id="gastgeber" class="gastgeber">
  <div class="block">
    <h2>{self.ui("g_titel", vermieter=True)}</h2>
    <p>{self.ui("g_text", vermieter=True)}</p>
    <p class="preis">{self.t(ang["preis"], vermieter=True)}</p>
    <a class="btn btn-hell" href="{E(self.portal_url())}">{self.ui("g_cta", vermieter=True)}</a>
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
        ang_url = self.portal_url()
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
""" + self.spiel_block() + f"""<section id="unterkuenfte" class="block">
  <h2>{self.ui("unterk_titel")}</h2>
  <div class="frei-grid">{frei}</div>
</section>
""" + self.gastgeber_block() + "</main>\n" + self.fuss(fotos))

    def spiel_block(self):
        sp = self.p.get("spiel")
        if not sp:
            return ""
        video = (f'<video class="spiel-video" src="{E(sp["video"])}" poster="{E(sp.get("poster", ""))}" autoplay muted loop playsinline preload="metadata" aria-hidden="true"></video>'
                 if sp.get("video") else "")
        return f"""<section id="spiel" class="block">
  <a class="spiel-teaser{" mit-video" if video else ""}" href="{E(sp["datei"])}">
    {video}<div class="spiel-text">
    <h2>{self.t(sp["titel"])}</h2>
    <p>{self.t(sp["text"])}</p>
    <span class="btn btn-hell">{self.t(sp["cta"])}</span>
    </div>
  </a>
</section>
"""

    def aktuell(self):
        p = self.p
        s0 = self.sp[0]
        titel = f'{p["marke"]} – {UI[s0]["news_titel"].format(ri=self.region_in(s0))}'
        return (self.kopf(titel, titel, aktiv="aktuell") + "<main>\n" + self.news_block() + self.karte_block()
                + self.gastgeber_block() + "</main>\n" + self.fuss(self.fotos()))

    # ---------- Vermieter-Seite (für Portale ohne eigene Webdesign-Seite) ----------
    def vermieter(self):
        p, cfg = self.p, self.cfg
        alt_sp, self.sp = self.sp, [s for s in self.vsp if s in VT] or ["en"]
        m = p["marke"]
        def v(k, **kw):
            return "".join(f'<span lang="{s}"{"" if i == 0 else " hidden"}>{E(VT[s][k].format(m=m, **kw))}</span>' for i, s in enumerate(self.sp))
        def opt(k):
            return f'<label class="zopt"><input type="checkbox" value="{k}" data-t="{E(VT["de"][k])}"> {v(k)}{" <small class=muted>(" + v("bald") + ")</small>" if k == "z_anfrage" else ""}</label>'
        bsp = "https://xn--ostseebad-mnchgut-9zb.de/inselzeit-moenchgut.html"
        komplett = "https://ruegenwebdesign.de/#lBeispiele"
        kontakt = cfg["kontakt_email"]
        pakete = [("p1", "p1t", True), ("p2", "p2t", True), ("p3", "p3t", False)]
        prk = {"p1": "pr1", "p2": "pr2", "p3": "pr3"}
        karten = "".join(f'''<div class="pk"><h3>{v(a)}</h3><span class="prov">{v("prov")}</span><div class="pr">{v(prk[a])}</div><p>{v(b)}</p>{('<div class="gratis">' + v("gratis") + '</div>') if g else ""}<a class="btn{"" if g else " ghost"}" href="{E(self.portal_url()) if g else "#anfrage"}" data-paket="{a}">{v("test_btn") if g else v("anfrage_btn")}</a></div>''' for a, b, g in pakete)
        sel = "".join(f'<option value="{a}">{E(VT[self.sp[0]][a])}</option>' for a, _, _ in pakete)
        html = self.kopf(f'{m} – {VT[self.sp[0]]["titel"].format(m=m)}', VT[self.sp[0]]["sub"], aktiv="recht") + f'''<main class="vm">
<section class="hero vm-hero"><div class="hero-inhalt"><h1>{v("titel")}</h1><p>{v("sub")}</p><div class="hero-btns"><a class="btn" href="{E(self.portal_url())}">{v("test_btn")}</a><a class="btn btn-rand" href="#anfrage">{v("cta")}</a></div></div></section>
<section class="block"><h2>{v("pakete")}</h2><div class="pk-grid">{karten}</div>
<div class="hinweis-box"><h3>{v("voll_t")}</h3><p>{v("voll_x")}</p>
<div class="hl-grid"><div class="hl"><div class="hl-text"><h3>{v("partner_t")}</h3><p>{v("partner_x")}</p></div></div><div class="hl"><div class="hl-text"><h3>{v("stand_t")}</h3><p>{v("stand_x")}</p></div></div></div></div></section>
<section class="block"><h2>{v("bsp_t")}</h2><p>{v("bsp_x")}</p>
<div class="framewrap"><iframe src="{bsp}" title="Beispiel" loading="lazy"></iframe></div>
<p><a href="{komplett}" target="_blank" rel="noopener">{v("bsp_link")}</a></p></section>
<section class="block"><h2>{v("zus_t")}</h2><p>{v("zus_x")}</p><div class="zopts">{"".join(opt(k) for k in ["z_anfrage","z_taxe","z_anz","z_gruss","z_ical"])}</div></section>
<section class="block" id="anfrage"><h2>{v("form_t")}</h2>
<form class="vform" id="vform" data-mail="{E(kontakt)}" data-marke="{E(m)}">
<label>{v("f_name")}<input name="name" required autocomplete="name"></label>
<label>{v("f_mail")}<input name="mail" type="email" required autocomplete="email"></label>
<label>{v("f_tel")}<input name="tel" type="tel" autocomplete="tel"></label>
<label>{v("f_anz")}<input name="anz" type="number" min="1" value="1"></label>
<label>{v("f_paket")}<select name="paket">{sel}</select></label>
<label class="voll">{v("f_msg")}<textarea name="msg" rows="3"></textarea></label>
<button class="btn" type="submit">{v("f_send")}</button><p class="ok" hidden>{v("f_ok")}</p></form>
<p class="klein"><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a> · <a href="https://ruegenwebdesign.de/#agb" target="_blank" rel="noopener">{v("agb")}</a></p></section>
</main>
''' + self.fuss([])
        self.sp = alt_sp
        return html

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

    def ds_plus(self):
        return 1 if self.p.get("spiel") else 0

    def spiel_datenschutz(self):
        if not self.p.get("spiel"):
            return ""
        return """<h2>5. Strategiespiel: Orte, Wetter und Bestenliste</h2>
<p>Das Strategiespiel (spiel.html) ist kostenlos und ohne Anmeldung nutzbar. Es lädt beim Öffnen keine Daten von Dritten.</p>
<p><b>Orte („Entdecken“):</b> Erst wenn Sie in der Leiste „Entdecken“ eine Kategorie wie Museen oder Bahnhöfe antippen, fragt Ihr Browser die Orte im sichtbaren Kartenausschnitt bei einem öffentlichen Overpass-Server für OpenStreetMap-Daten ab (overpass-api.de, Deutschland; ersatzweise overpass.kumi.systems, Österreich). Dabei werden Ihre IP-Adresse und der Kartenausschnitt übertragen. Die Daten stammen von den OpenStreetMap-Mitwirkenden (Lizenz ODbL).</p>
<p><b>Wetter:</b> Erst wenn Sie „Wetter“ antippen, ruft Ihr Browser aktuelle Wetterwerte für die Gebiete des Spiels bei Open-Meteo (open-meteo.com, Schweiz) ab. Dabei werden Ihre IP-Adresse und die Koordinaten der Gebiete übertragen, nicht Ihr Standort.</p>
<p>Rechtsgrundlage für beide Abrufe ist Ihre Einwilligung durch das Antippen (Art. 6 Abs. 1 lit. a DSGVO). Sie können die Kategorie jederzeit wieder ausschalten; dann finden keine weiteren Abrufe statt.</p>
<p><b>Gästebewertungen (Google):</b> Unter „Top 10“ → „Gästebewertungen“ sendet Ihr Browser den sichtbaren Kartenausschnitt (Koordinaten) und die Sprache an unseren Vermittlungsdienst bei Cloudflare (Cloudflare, Inc., USA; Auftragsverarbeitung, EU-Standardvertragsklauseln). Dieser fragt bei der Google Places API (Google Ireland Limited, Dublin) die Bewertungen der Restaurants in diesem Ausschnitt ab. Ihre IP-Adresse erhält Google dabei nicht, nur Cloudflare für die technische Auslieferung. Rechtsgrundlage ist unser berechtigtes Interesse an einem nützlichen Gästeangebot (Art. 6 Abs. 1 lit. f DSGVO). Das Ergebnis wird nur für die laufende Sitzung im Speicher Ihres Browsers gehalten.</p>
<p><b>Straßenkarte:</b> Wenn Sie sehr nah heranzoomen, fragt das Spiel, ob es eine Straßenkarte laden soll. Erst wenn Sie „Laden“ antippen oder den Schalter „Straßenkarte“ einschalten, lädt Ihr Browser Kartenkacheln von tile.openstreetmap.org (OpenStreetMap Foundation, Vereinigtes Königreich); dabei wird Ihre IP-Adresse übertragen. Ihre Wahl wird im Speicher Ihres Browsers vermerkt.</p>
<p><b>Route planen:</b> Der Knopf „Route planen“ ist ein einfacher Link zu Google Maps. Daten gehen erst an Google, wenn Sie ihn antippen; dann gilt die Datenschutzerklärung von Google.</p>
<p><b>Bestenliste und Spracheinstellung:</b> Ihr Spielername, Ihre Punkte und die gewählte Sprache werden nur im Speicher Ihres Browsers (localStorage) auf Ihrem Gerät abgelegt und nicht an uns oder Dritte übertragen. Die übrigen Namen in der Bestenliste sind als „Computer“ gekennzeichnete Spielgegner. Sie können die Einträge löschen, indem Sie die Website-Daten in Ihrem Browser löschen.</p>"""

    def datenschutz(self):
        b = self.cfg["betreiber"]
        return self.kopf(f'Datenschutz – {self.p["marke"]}', "Datenschutzerklärung", aktiv="recht") + f"""<main class="block recht">
<h1>Datenschutzerklärung</h1>
<p class="klein">Stand: {MONATE[HEUTE.month - 1]} {HEUTE.year}</p>
<h2>1. Verantwortlicher</h2>
<p>{E(b["name"])}, {E(b["strasse"])}, {E(b["ort"])}, E-Mail: {E(b["email"])}</p>
<h2>2. Das Wichtigste in Kürze</h2>
<p>Diese Website setzt keine Cookies, kein Tracking und keine Analyse-Werkzeuge ein. Schriften, Kartenbibliothek und Fotos werden von unserem eigenen Webspace geladen. Nur wenn Sie die Karte ausdrücklich laden, werden Kartenkacheln von OpenStreetMap abgerufen.{' Ebenso werden im Strategiespiel Orte und Wetter erst abgerufen, wenn Sie diese antippen.' if self.p.get('spiel') else ''}</p>
<h2>3. Hosting und Server-Logfiles</h2>
<p>Die Website wird über GitHub Pages bereitgestellt (GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). Beim Aufruf verarbeitet GitHub technisch notwendige Daten wie IP-Adresse, Zeitpunkt und aufgerufene Seite, um die Seite auszuliefern und die Sicherheit zu gewährleisten (Art. 6 Abs. 1 lit. f DSGVO).</p>
<h2>4. Karte (OpenStreetMap)</h2>
<p>Die Karte wird erst nach Klick auf „Karte laden“ angezeigt. Dann werden Kartenkacheln von Servern der OpenStreetMap Foundation (St John’s Innovation Centre, Cowley Road, Cambridge, CB4 0WS, Vereinigtes Königreich) geladen; dabei wird Ihre IP-Adresse übertragen (Art. 6 Abs. 1 lit. a DSGVO – Ihre Einwilligung durch den Klick).</p>
{self.spiel_datenschutz()}
<h2>{5 + self.ds_plus()}. Fotos</h2>
<p>Die Fotos stammen von Wikimedia Commons und werden unter den jeweils angegebenen freien Lizenzen genutzt. Sie liegen auf unserem eigenen Webspace; beim Anzeigen werden keine Daten an Wikimedia übertragen.</p>
<h2>{6 + self.ds_plus()}. Kontakt per E-Mail</h2>
<p>Wenn Sie uns schreiben, verarbeiten wir Ihre Angaben zur Bearbeitung Ihrer Anfrage (Art. 6 Abs. 1 lit. b DSGVO) und löschen sie, wenn sie nicht mehr benötigt werden.</p>
<h2>{7 + self.ds_plus()}. Übermittlung in Drittländer</h2>
<p>Für GitHub (USA) erfolgt die Übermittlung auf Grundlage des EU-US Data Privacy Framework bzw. von Standardvertragsklauseln. Für das Vereinigte Königreich{' und die Schweiz (Open-Meteo)' if self.p.get('spiel') else ''} besteht ein Angemessenheitsbeschluss der EU-Kommission.</p>
<h2>{8 + self.ds_plus()}. Ihre Rechte</h2>
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
    extra = ROOT / "extra" / p["repo"]  # feste Zusatzdateien, z. B. das Vermietungsportal auf eu-bnb.com/vermieten
    if extra.is_dir():
        shutil.copytree(extra, ziel, dirs_exist_ok=True)
    (ziel / "impressum.html").write_text(s.impressum(), encoding="utf-8")
    (ziel / "datenschutz.html").write_text(s.datenschutz(), encoding="utf-8")
    orte = ROOT / "content" / "orte" / f"{p['repo']}.json" if "ROOT" in globals() else None
    if p.get("spiel") and orte and orte.exists():
        shutil.copy(orte, ziel / "orte.json")
    if p.get("angebot") == "allgemein":
        (ziel / "vermieter.html").write_text(s.vermieter(), encoding="utf-8")
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


def logo_html(m):
    """Marke zweifarbig: Vorderteil in Markenfarbe, „BnB“ in Akzentfarbe (wie SyltBnB)."""
    i = m.rfind("BnB")
    return E(m) if i <= 0 else f'{E(m[:i])}<span>{E(m[i:])}</span>'


def main(argv):
    cfg = config.lade(mit_umleitungen=True)
    alle = [p for p in cfg["portale"] if not p.get("umleitung")]
    auswahl = [p for p in cfg["portale"] if not argv or p["slug"].split("~")[0] in argv]
    for p in auswahl:
        ziel = baue_umleitung(p) if p.get("umleitung") else baue(cfg, p, alle)
        print(f"✓ {p['slug']:12} → {ziel.relative_to(ROOT)}  ({p['modus']})")


if __name__ == "__main__":
    main(sys.argv[1:])
