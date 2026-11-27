// places-proxy – Cloudflare Worker für die Gästebewertungen (Top 10 Restaurants) in den Strategiespielen.
// Der Google-Schlüssel liegt nur hier als Secret GOOGLE_PLACES_KEY. Gäste-IPs gehen nicht an Google.
// Einstellbar ohne Code-Änderung (Worker → Settings → Variables):
//   MAX_PAGES  = Google-Anfragen je geöffneter Liste (1–3, Standard 3; je Anfrage 20 Restaurants)
//   MIN_REVIEWS = Mindestzahl Bewertungen (Standard 20)
//   TOP_N      = Länge der Liste (Standard 20)
// Zusätzlich /fussball: Spiele und Ergebnisse der Stadion-Vereine aus OpenLigaDB (frei, ohne Schlüssel).
const ERLAUBT = ["a-bnb.com", "ch-bnb.com", "dk-bnb.dk", "es-bnb.com", "fi-bnb.com", "fr-bnb.com", "friesh-stack.github.io", "gr-bnb.com", "h-bnb.com", "hamburgbnb.de", "it-bnb.com", "muenchenbnb.de", "no-bnb.com", "ostseebnb.de", "p-bnb.com", "se-bnb.com", "xn--ostseebad-mnchgut-9zb.de"];
const okOrigin = o => { try { const h = new URL(o).hostname; return ERLAUBT.some(d => h === d || h.endsWith('.' + d)) } catch (e) { return false } };
const cors = o => ({ 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (d, o, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(o) } });

// ---------- Fußball (OpenLigaDB) ----------
const VEREINE = { HSV: /hamburger sv/i, STP: /st\.? ?pauli/i, FCB: /bayern m(ü|u)nchen/i, M60: /1860/i };
const LIGEN = ['bl1', 'bl2', 'bl3'];
let FB_CACHE = { t: 0, d: null };
async function ligaSpiele() {
  if (FB_CACHE.d && Date.now() - FB_CACHE.t < 5 * 60 * 1000) return FB_CACHE.d;
  const n = new Date(), saison = n.getUTCMonth() >= 6 ? n.getUTCFullYear() : n.getUTCFullYear() - 1, alle = [];
  for (const l of LIGEN) {
    try { const r = await fetch(`https://api.openligadb.de/getmatchdata/${l}/${saison}`, { cf: { cacheTtl: 300 } }); if (r.ok) alle.push(...(await r.json())) } catch (e) { }
  }
  FB_CACHE = { t: Date.now(), d: alle }; return alle;
}
const stand = m => {
  const end = (m.matchResults || []).find(r => r.resultTypeID === 2) || (m.matchResults || []).slice(-1)[0];
  if (m.matchIsFinished && end) return [end.pointsTeam1, end.pointsTeam2];
  const g = (m.goals || []).slice(-1)[0]; return g ? [g.scoreTeam1, g.scoreTeam2] : [0, 0];
};
const kurz = m => ({ t: m.matchDateTimeUTC, liga: m.leagueName, h: m.team1.teamName, a: m.team2.teamName, hi: m.team1.teamIconUrl, ai: m.team2.teamIconUrl });
async function fussball(ids) {
  const alle = await ligaSpiele(), jetzt = Date.now(), out = {};
  for (const id of ids) {
    const re = VEREINE[id]; if (!re) continue;
    const sp = alle.filter(m => re.test(m.team1.teamName) || re.test(m.team2.teamName)).sort((a, b) => Date.parse(a.matchDateTimeUTC) - Date.parse(b.matchDateTimeUTC));
    const fertig = sp.filter(m => m.matchIsFinished), offen = sp.filter(m => !m.matchIsFinished);
    const live = offen.filter(m => { const t = Date.parse(m.matchDateTimeUTC); return t <= jetzt && jetzt - t < 150 * 60 * 1000 });
    out[id] = {
      letzte: fertig.slice(-3).reverse().map(m => ({ ...kurz(m), s: stand(m) })),
      live: live.map(m => ({ ...kurz(m), s: stand(m) })),
      naechste: offen.filter(m => Date.parse(m.matchDateTimeUTC) > jetzt).slice(0, 3).map(kurz)
    };
  }
  return out;
}

export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url);
    if (!okOrigin(o)) return new Response('forbidden', { status: 403 });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    if (url.pathname === '/ok') return json({ ok: !!env.GOOGLE_PLACES_KEY }, o);
    if (url.pathname === '/fussball') { const ids = (url.searchParams.get('v') || '').split(',').filter(Boolean).slice(0, 6); return json(await fussball(ids), o) }
    if (url.pathname !== '/top' || req.method !== 'POST') return json({ error: 'not found' }, o, 404);
    let b; try { b = await req.json() } catch (e) { return json({ error: 'bad request' }, o, 400) }
    const n = x => Number.isFinite(+x) ? +x : NaN, S = n(b.S), W = n(b.W), N = n(b.N), E = n(b.E);
    if ([S, W, N, E].some(isNaN) || N <= S || E <= W || N - S > 3 || E - W > 5) return json({ error: 'area' }, o, 400);
    const lang = /^[a-z]{2}$/.test(b.lang || '') ? b.lang : 'de';
    const pages = Math.max(1, Math.min(3, parseInt(env.MAX_PAGES || '3', 10) || 3)), minR = parseInt(env.MIN_REVIEWS || '20', 10) || 20;
    let all = [], tok = '';
    for (let p = 0; p < pages; p++) {
      const body = { textQuery: 'best restaurants', includedType: 'restaurant', strictTypeFiltering: true, pageSize: 20, languageCode: lang,
        locationRestriction: { rectangle: { low: { latitude: S, longitude: W }, high: { latitude: N, longitude: E } } } };
      if (tok) body.pageToken = tok;
      const r = await fetch('https://places.googleapis.com/v1/places:searchText', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Goog-Api-Key': env.GOOGLE_PLACES_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.rating,places.userRatingCount,places.googleMapsUri,nextPageToken' }, body: JSON.stringify(body) });
      if (!r.ok) { if (!all.length) return json({ error: 'google', status: r.status }, o, 502); break }
      const j = await r.json(); all = all.concat(j.places || []); tok = j.nextPageToken; if (!tok) break;
    }
    const seen = new Set();
    const L = all.filter(x => x.rating && x.userRatingCount >= minR && !seen.has(x.id) && seen.add(x.id))
      .sort((a, c) => c.rating - a.rating || c.userRatingCount - a.userRatingCount).slice(0, Math.max(5, Math.min(30, parseInt(env.TOP_N || '20', 10) || 20)))
      .map(x => [x.displayName && x.displayName.text || '', x.location.latitude, x.location.longitude, x.rating, x.userRatingCount, x.googleMapsUri || '']);
    return json({ L, min: minR }, o);
  }
};
