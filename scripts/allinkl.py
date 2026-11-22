#!/usr/bin/env python3
"""Richtet die Domains bei All-Inkl automatisch über die KAS-API ein.

modus "dns" (empfohlen): Domain zeigt direkt auf GitHub Pages – Adresszeile bleibt z. B. hamburgbnb.de
    @    A     185.199.108.153 / .109 / .110 / .111   (GitHub Pages)
    @    AAAA  2606:50c0:8000::153 … 8003::153
    www  CNAME <owner>.github.io.
modus "weiterleitung": 301-Weiterleitung auf https://<owner>.github.io/<repo>/
    (dann darf im Repo KEINE CNAME-Datei liegen – build.py beachtet das)

Umgebung: KAS_LOGIN (z. B. w0123456), KAS_PASSWORT
Aufruf:   python scripts/allinkl.py                 (Probelauf: zeigt nur, was passieren würde)
          python scripts/allinkl.py --anwenden      (führt die Änderungen aus)
          python scripts/allinkl.py hamburg --anwenden
Hinweis:  Mit aktivierter Zwei-Faktor-Anmeldung im KAS funktioniert die Automatik nicht.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
GH_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
GH_AAAA = ["2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153"]

HUELLE = ('<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
          'xmlns:ns1="{ns}" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
          'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
          '<SOAP-ENV:Body><ns1:{fn}><Params xsi:type="xsd:string">{json}</Params></ns1:{fn}></SOAP-ENV:Body></SOAP-ENV:Envelope>')


class KasFehler(Exception):
    pass


def _lokal(tag):
    return tag.rsplit("}", 1)[-1]


def _wandle(el):
    items = [c for c in el if _lokal(c.tag) == "item"]
    if not items:
        return (el.text or "").strip()
    if all(any(_lokal(x.tag) == "key" for x in it) for it in items):
        out = {}
        for it in items:
            k = next(x for x in it if _lokal(x.tag) == "key").text
            v = next((x for x in it if _lokal(x.tag) == "value"), None)
            out[k] = _wandle(v) if v is not None else ""
        return out
    return [_wandle(it) for it in items]


class Kas:
    def __init__(self, login, passwort):
        self.login, self.passwort, self.token, self.pause = login, passwort, None, 1.0

    def _soap(self, url, ns, fn, params):
        body = HUELLE.format(ns=ns, fn=fn, json=escape(json.dumps(params)))
        req = urllib.request.Request(url, data=body.encode(), headers={
            "Content-Type": "text/xml; charset=utf-8", "SOAPAction": f"{ns}#{fn}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                xml = r.read()
        except urllib.error.HTTPError as e:
            xml = e.read()
        wurzel = ET.fromstring(xml)
        for el in wurzel.iter():
            if _lokal(el.tag) == "faultstring":
                raise KasFehler(el.text)
        ret = next(el for el in wurzel.iter() if _lokal(el.tag) == "return")
        return ret

    def anmelden(self):
        ret = self._soap("https://kasapi.kasserver.com/soap/KasAuth.php", "urn:xmethodsKasApiAuthentication", "KasAuth",
                         {"kas_login": self.login, "kas_auth_type": "plain", "kas_auth_data": self.passwort,
                          "session_lifetime": 1800, "session_update_lifetime": "Y"})
        self.token = (ret.text or "").strip()

    def __call__(self, aktion, params=None):
        if not self.token:
            self.anmelden()
        for versuch in range(3):
            try:
                time.sleep(self.pause)
                ret = self._soap("https://kasapi.kasserver.com/soap/KasApi.php", "urn:xmethodsKasApi", "KasApi",
                                 {"kas_login": self.login, "kas_auth_type": "session", "kas_auth_data": self.token,
                                  "kas_action": aktion, "KasRequestParams": params or {}})
                antwort = _wandle(ret).get("Response", {})
                try:
                    self.pause = max(1.0, float(antwort.get("KasFloodDelay", 1)))
                except (TypeError, ValueError):
                    pass
                return antwort.get("ReturnInfo")
            except KasFehler as e:
                if str(e) == "flood_protection" and versuch < 2:
                    time.sleep(5)
                    continue
                raise


def dns_einrichten(kas, p, owner, anwenden):
    zone = p["domain"] + "."
    ziel_www = f"{owner}.github.io."
    records = kas("get_dns_settings", {"zone_host": zone}) or []
    if isinstance(records, dict):
        records = [records]
    plan = []  # (beschreibung, aktion, params)

    def name(r):
        return (r.get("record_name") or "").rstrip(".")

    for typ, soll in (("A", GH_A), ("AAAA", GH_AAAA)):
        ist = [r for r in records if name(r) in ("", "@") and r.get("record_type") == typ]
        for r in ist:
            if r.get("record_data") not in soll:
                plan.append((f"löschen  @ {typ} {r.get('record_data')}", "delete_dns_settings", {"record_id": r["record_id"]}, r))
        for ip in soll:
            if not any(r.get("record_data") == ip for r in ist):
                plan.append((f"anlegen  @ {typ} {ip}", "add_dns_settings",
                             {"zone_host": zone, "record_name": "", "record_type": typ, "record_data": ip, "record_aux": 0}, None))

    www = [r for r in records if name(r) == "www"]
    cname = [r for r in www if r.get("record_type") == "CNAME"]
    for r in www:
        if r.get("record_type") in ("A", "AAAA"):
            plan.append((f"löschen  www {r['record_type']} {r.get('record_data')}", "delete_dns_settings", {"record_id": r["record_id"]}, r))
    if cname:
        if cname[0].get("record_data", "").rstrip(".") != ziel_www.rstrip("."):
            plan.append((f"ändern   www CNAME → {ziel_www}", "update_dns_settings",
                         {"record_id": cname[0]["record_id"], "record_data": ziel_www}, cname[0]))
    else:
        plan.append((f"anlegen  www CNAME {ziel_www}", "add_dns_settings",
                     {"zone_host": zone, "record_name": "www", "record_type": "CNAME", "record_data": ziel_www, "record_aux": 0}, None))

    # Reihenfolge: erst neue Apex-Einträge (kein Ausfall), dann löschen, zuletzt www-CNAME
    plan.sort(key=lambda x: 0 if x[1] == "add_dns_settings" and x[2]["record_type"] != "CNAME" else (1 if x[1] == "delete_dns_settings" else 2))
    if not plan:
        print("  = DNS zeigt bereits auf GitHub Pages")
    for text, aktion, params, alt in plan:
        if alt is not None and alt.get("record_changeable") == "N":
            print(f"  ! {text} – Eintrag ist im KAS gesperrt, bitte von Hand ändern")
            continue
        print(f"  {'→' if anwenden else '(Probe)'} {text}")
        if anwenden:
            try:
                kas(aktion, params)
            except KasFehler as e:
                print(f"    ! {e}")


def weiterleitung_einrichten(kas, p, owner, anwenden):
    ziel = f"https://{owner}.github.io/{p['repo']}/"
    print(f"  {'→' if anwenden else '(Probe)'} 301-Weiterleitung {p['domain']} → {ziel}")
    if not anwenden:
        return
    try:
        kas("update_domain", {"domain_name": p["domain"], "domain_path": ziel, "redirect_status": 301})
    except KasFehler as e:
        if "not_found" not in str(e):
            raise
        name, tld = p["domain"].split(".", 1)
        kas("add_domain", {"domain_name": name, "domain_tld": tld, "domain_path": ziel, "redirect_status": 301})


def main(argv):
    anwenden = "--anwenden" in argv
    slugs = [a for a in argv if not a.startswith("--")]
    cfg = json.loads((ROOT / "portale.json").read_text(encoding="utf-8"))
    cfg["portale"] = [p for p in cfg["portale"] if p.get("aktiv", True)]  # "aktiv": false = Portal pausiert
    kas = Kas(os.environ["KAS_LOGIN"].strip(), os.environ["KAS_PASSWORT"].strip())
    if not anwenden:
        print("PROBELAUF – es wird nichts geändert. Zum Ausführen: --anwenden\n")
    fehler = 0
    for p in cfg["portale"]:
        if slugs and p["slug"] not in slugs:
            continue
        print(f"{p['domain']} ({p['allinkl']})")
        try:
            if p["allinkl"] == "dns":
                dns_einrichten(kas, p, cfg["github_owner"], anwenden)
            else:
                weiterleitung_einrichten(kas, p, cfg["github_owner"], anwenden)
        except KasFehler as e:
            fehler += 1
            print(f"  ! {e}")
            if any(w in str(e) for w in ("password", "login", "auth", "session")):
                # Anmeldung falsch: sofort aufhören, damit das KAS-Konto nicht gesperrt wird
                print("\nAbbruch: KAS-Anmeldung fehlgeschlagen – bitte KAS_LOGIN / KAS_PASSWORT prüfen.")
                break
        except Exception as e:  # noqa: BLE001
            fehler += 1
            print(f"  ! {e}")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
