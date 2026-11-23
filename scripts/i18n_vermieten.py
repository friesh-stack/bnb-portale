#!/usr/bin/env python3
"""Erzeugt feste Übersetzungsdateien für das Vermietungsportal myburano.com/vermieten.

Öffnet das Portal je Sprache im Browser, lässt alle Ansichten einmal anzeigen,
übersetzt alle Texte (Claude Haiku) und lädt das Ergebnis als
vermieten/i18n/<sprache>.json ins Repo blue-lagune-burano hoch.
Danach erscheint jede Sprache sofort – ohne Kosten pro Besucher.

Umgebung: ANTHROPIC_API_KEY, GH_PAT
Aufruf:   python scripts/i18n_vermieten.py            (alle Sprachen)
          python scripts/i18n_vermieten.py it fr      (nur diese)
"""
import asyncio, base64, json, os, sys, urllib.request, urllib.error
from playwright.async_api import async_playwright

URL = "https://myburano.com/vermieten/"
REPO, PFAD = "friesh-stack/blue-lagune-burano", "vermieten/i18n/{}.json"
SPRACHEN = ["it", "en", "fr", "es", "nl", "da", "sv", "nb", "fi"]

def claude(body):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()

def gh(methode, pfad, daten=None):
    req = urllib.request.Request("https://api.github.com" + pfad, method=methode, data=json.dumps(daten).encode() if daten else None,
        headers={"Authorization": "Bearer " + os.environ["GH_PAT"], "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

async def sprache(browser, L):
    ctx = await browser.new_context(viewport={"width": 1200, "height": 900})
    async def route(r):
        if r.request.method == "POST" and "workers.dev" in r.request.url:
            body = json.loads(r.request.post_data)
            if "Translate these German" in json.dumps(body):
                antwort = await asyncio.to_thread(claude, body)
                await r.fulfill(status=200, content_type="application/json", body=antwort); return
            await r.abort(); return
        await r.continue_()
    await ctx.route("**/*", route)
    pg = await ctx.new_page()
    await pg.goto(URL + "?lang=" + L, wait_until="load"); await pg.wait_for_timeout(4000)
    # alle wichtigen Ansichten einmal zeigen, damit ihre Texte erfasst werden
    for js in ["showVm()", "openPaket('portal')", "closeM('mPaket')", "openPaket('website')", "closeM('mPaket')",
               "openPaket('service')", "closeM('mPaket')", "openInfo('agb')", "closeM('mInfo')", "openInfo('impressum')",
               "closeM('mInfo')", "openInfo('datenschutz')", "closeM('mInfo')", "showLogin()", "showVm()", "vOpen('vermieter')", "vClose()"]:
        try: await pg.evaluate(js)
        except Exception: pass
        await pg.wait_for_timeout(700)
    for _ in range(600):
        if await pg.evaluate("window.BW_PENDING?BW_PENDING():0") == 0: break
        await pg.wait_for_timeout(1000)
    daten = json.loads(await pg.evaluate(f"localStorage.getItem('bw_i18n_{L}')||'{{}}'"))
    await ctx.close()
    return daten

async def main(liste):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for L in liste:
            neu = await sprache(browser, L)
            alt = gh("GET", f"/repos/{REPO}/contents/" + PFAD.format(L))
            daten = json.loads(base64.b64decode(alt["content"])) if alt else {}
            daten.update(neu)
            inhalt = json.dumps(daten, ensure_ascii=False, indent=0, sort_keys=True).encode()
            gh("PUT", f"/repos/{REPO}/contents/" + PFAD.format(L), {"message": f"auto: Übersetzung Vermietungsportal {L}",
               "content": base64.b64encode(inhalt).decode(), **({"sha": alt["sha"]} if alt else {})})
            print(f"✓ {L}: {len(daten)} Texte")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main([a for a in sys.argv[1:] if a in SPRACHEN] or SPRACHEN))
