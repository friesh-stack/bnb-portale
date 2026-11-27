// places-proxy – Cloudflare Worker für die Gästebewertungen (Top 10 Restaurants) in den Strategiespielen.
// Der Google-Schlüssel liegt nur hier als Secret GOOGLE_PLACES_KEY. Gäste-IPs gehen nicht an Google.
// Einstellbar ohne Code-Änderung (Worker → Settings → Variables):
//   MAX_PAGES  = Google-Anfragen je geöffneter Liste (1–3, Standard 3; je Anfrage 20 Restaurants)
//   MIN_REVIEWS = Mindestzahl Bewertungen (Standard 20)
const ERLAUBT = ["a-bnb.com", "ch-bnb.com", "dk-bnb.dk", "es-bnb.com", "fi-bnb.com", "fr-bnb.com", "friesh-stack.github.io", "gr-bnb.com", "h-bnb.com", "hamburgbnb.de", "it-bnb.com", "muenchenbnb.de", "no-bnb.com", "ostseebnb.de", "p-bnb.com", "se-bnb.com", "xn--ostseebad-mnchgut-9zb.de"];
const okOrigin = o => { try { const h = new URL(o).hostname; return ERLAUBT.some(d => h === d || h.endsWith('.' + d)) } catch (e) { return false } };
const cors = o => ({ 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (d, o, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(o) } });

export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url);
    if (!okOrigin(o)) return new Response('forbidden', { status: 403 });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    if (url.pathname === '/ok') return json({ ok: !!env.GOOGLE_PLACES_KEY }, o);
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
      .sort((a, c) => c.rating - a.rating || c.userRatingCount - a.userRatingCount).slice(0, 10)
      .map(x => [x.displayName && x.displayName.text || '', x.location.latitude, x.location.longitude, x.rating, x.userRatingCount, x.googleMapsUri || '']);
    return json({ L, min: minR }, o);
  }
};
