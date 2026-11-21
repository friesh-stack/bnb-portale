# bnb-portale – Steuerzentrale für alle Gästeportale

Ein Repo steuert alle Domains. Jeden Morgen läuft automatisch:

1. **Fotos** – fehlende Regionsfotos von Wikimedia Commons (freie Lizenz, Urheber im Fuß)
2. **News** – „Aktuell“ per Claude mit Websuche (täglich bzw. wöchentlich je Portal)
3. **Bauen** – Seiten aus `portale.json` erzeugen
4. **GitHub** – je Domain ein Repo, nur geänderte Dateien, ein Commit, Pages + eigene Domain
5. **All-Inkl** (nur auf Knopfdruck) – DNS auf GitHub Pages oder 301-Weiterleitung über die KAS-API

## Einmalig einrichten (Settings → Secrets and variables → Actions)

| Secret | Inhalt |
|---|---|
| `GH_PAT` | Fine-grained Token für friesh-stack, „All repositories“, Rechte: Administration, Contents, Pages = Read and write |
| `ANTHROPIC_API_KEY` | Claude-API-Schlüssel (derselbe wie im Worker) |
| `KAS_LOGIN` | KAS-Login, z. B. w0123456 |
| `KAS_PASSWORT` | KAS-Passwort (Zwei-Faktor im KAS muss aus sein) |

Danach: **Actions → Gästeportale → Run workflow** – erst mit All-Inkl „probelauf“, Ausgabe prüfen, dann „anwenden“.

## Neue Domain hinzufügen
In `portale.json` einen Block kopieren, `slug`, `domain`, `repo`, Texte, Karte und Pfeile anpassen, speichern – der Rest passiert von selbst.

- `modus: "neu"` – komplette Seite wird erzeugt
- `modus: "bestand"` – vorhandene `index.html` bleibt unangetastet, dazu kommen `aktuell.html`, `impressum.html`, `datenschutz.html`
- `allinkl: "dns"` – Adresszeile zeigt die eigene Domain (empfohlen)
- `allinkl: "weiterleitung"` – 301 auf `friesh-stack.github.io/<repo>/`

## Von Hand (lokal)
```
python scripts/fotos.py            # Fotos
python scripts/news.py hamburg     # News für ein Portal
python scripts/build.py            # bauen → dist/
python scripts/github_deploy.py --probe
python scripts/allinkl.py          # Probelauf
```
