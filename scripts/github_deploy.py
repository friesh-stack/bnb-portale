#!/usr/bin/env python3
"""Lädt dist/<repo>/ automatisch zu GitHub hoch – ein Commit pro Portal.

- legt fehlende Repos an (öffentlich, für GitHub Pages)
- lädt nur geänderte Dateien hoch
- modus "bestand": index.html, CNAME und README.md im Repo werden NIE überschrieben
- schaltet GitHub Pages ein und setzt die eigene Domain (modus "neu" + allinkl "dns")

Umgebung: GH_PAT  (Fine-grained Token: Administration, Contents, Pages = Read & write)
Aufruf:   python scripts/github_deploy.py            (alle)
          python scripts/github_deploy.py hamburg    (nur dieses)
          python scripts/github_deploy.py --probe    (nur anzeigen, nichts hochladen)
"""
import base64
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
GESCHUETZT = {"index.html", "CNAME", "README.md"}


class GH:
    def __init__(self, token):
        self.token = token

    def __call__(self, methode, pfad, daten=None, ok404=False):
        req = urllib.request.Request(API + pfad, method=methode,
                                     data=json.dumps(daten).encode() if daten is not None else None,
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                inhalt = r.read()
                return json.loads(inhalt) if inhalt else {}
        except urllib.error.HTTPError as e:
            if ok404 and e.code == 404:
                return None
            raise RuntimeError(f"{methode} {pfad} → {e.code}: {e.read().decode()[:300]}") from None


def blob_sha(daten: bytes):
    return hashlib.sha1(b"blob %d\0" % len(daten) + daten).hexdigest()


def repo_sicherstellen(gh, owner, p, probe):
    repo = gh("GET", f"/repos/{owner}/{p['repo']}", ok404=True)
    if repo:
        return repo
    print(f"  + Repo {owner}/{p['repo']} wird angelegt")
    if probe:
        return None
    konto = gh("GET", f"/users/{owner}")
    ziel = f"/orgs/{owner}/repos" if konto.get("type") == "Organization" else "/user/repos"
    gh("POST", ziel, {"name": p["repo"], "description": f"Gästeportal {p['domain']}", "homepage": f"https://{p['domain']}",
                      "private": False, "auto_init": True})
    time.sleep(3)
    return gh("GET", f"/repos/{owner}/{p['repo']}")


def hochladen(gh, owner, p, repo, probe):
    quelle = ROOT / "dist" / p["repo"]
    branch = repo["default_branch"] if repo else "main"
    vorhanden = {}
    if repo:
        ref = gh("GET", f"/repos/{owner}/{p['repo']}/git/ref/heads/{branch}")
        basis_commit = ref["object"]["sha"]
        basis_tree = gh("GET", f"/repos/{owner}/{p['repo']}/git/commits/{basis_commit}")["tree"]["sha"]
        baum = gh("GET", f"/repos/{owner}/{p['repo']}/git/trees/{basis_tree}?recursive=1")
        vorhanden = {e["path"]: e["sha"] for e in baum.get("tree", []) if e["type"] == "blob"}
    neue = []
    for datei in sorted(quelle.rglob("*")):
        if not datei.is_file():
            continue
        pfad = datei.relative_to(quelle).as_posix()
        if p["modus"] == "bestand" and pfad in GESCHUETZT:
            continue
        inhalt = datei.read_bytes()
        if vorhanden.get(pfad) == blob_sha(inhalt):
            continue
        neue.append((pfad, inhalt))
    if not neue:
        print("  = keine Änderungen")
        return
    print(f"  ↑ {len(neue)} Dateien: " + ", ".join(x[0] for x in neue[:8]) + (" …" if len(neue) > 8 else ""))
    if probe:
        return
    eintraege = []
    for pfad, inhalt in neue:
        blob = gh("POST", f"/repos/{owner}/{p['repo']}/git/blobs",
                  {"content": base64.b64encode(inhalt).decode(), "encoding": "base64"})
        eintraege.append({"path": pfad, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = gh("POST", f"/repos/{owner}/{p['repo']}/git/trees", {"base_tree": basis_tree, "tree": eintraege})
    commit = gh("POST", f"/repos/{owner}/{p['repo']}/git/commits",
                {"message": f"auto: Inhalte {dt.date.today().isoformat()}", "tree": tree["sha"], "parents": [basis_commit]})
    gh("PATCH", f"/repos/{owner}/{p['repo']}/git/refs/heads/{branch}", {"sha": commit["sha"]})
    print(f"  ✓ Commit {commit['sha'][:7]}")


def pages_einschalten(gh, owner, p, repo, probe):
    if probe or not repo:
        return
    pages = gh("GET", f"/repos/{owner}/{p['repo']}/pages", ok404=True)
    if not pages:
        gh("POST", f"/repos/{owner}/{p['repo']}/pages", {"source": {"branch": repo["default_branch"], "path": "/"}})
        print("  ✓ GitHub Pages eingeschaltet")
        pages = gh("GET", f"/repos/{owner}/{p['repo']}/pages", ok404=True) or {}
    if p["allinkl"] == "dns" and pages.get("cname") != p["domain"]:
        gh("PUT", f"/repos/{owner}/{p['repo']}/pages", {"cname": p["domain"]})
        print(f"  ✓ Eigene Domain {p['domain']} gesetzt")
    elif p["allinkl"] == "dns" and not pages.get("https_enforced"):
        try:  # klappt erst, wenn das Zertifikat da ist (nach DNS-Umstellung, bis ~24 h)
            gh("PUT", f"/repos/{owner}/{p['repo']}/pages", {"https_enforced": True})
            print("  ✓ HTTPS erzwungen")
        except RuntimeError:
            print("  … HTTPS folgt, sobald GitHub das Zertifikat ausgestellt hat")


def main(argv):
    probe = "--probe" in argv
    slugs = [a for a in argv if not a.startswith("--")]
    cfg = json.loads((ROOT / "portale.json").read_text(encoding="utf-8"))
    cfg["portale"] = [p for p in cfg["portale"] if p.get("aktiv", True)]  # "aktiv": false = Portal pausiert
    gh = GH(os.environ.get("GH_PAT", ""))
    owner = cfg["github_owner"]
    fehler = 0
    for p in cfg["portale"]:
        if slugs and p["slug"] not in slugs:
            continue
        print(f"{p['repo']} ({p['domain']})")
        try:
            repo = repo_sicherstellen(gh, owner, p, probe)
            hochladen(gh, owner, p, repo, probe)
            pages_einschalten(gh, owner, p, repo, probe)
        except Exception as e:  # noqa: BLE001
            fehler += 1
            print(f"  ! {e}")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
