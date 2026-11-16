#!/usr/bin/env python3
"""Update existing SmartTV entries from iptv-org Argentina, Mexico and US lists.

Only exact tvg-id matches are eligible. The script never adds or deletes channels.
If no reachable replacement is found, the current URL is kept.
"""
import re
import urllib.request
from pathlib import Path

PLAYLIST = Path("SmartTV.m3u")
SOURCE_URLS = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://iptv-org.github.io/iptv/countries/mx.m3u",
    "https://iptv-org.github.io/iptv/countries/us.m3u",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 SmartTV-Playlist-Updater",
    "Range": "bytes=0-0",
}


def fetch_text(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def reachable(url):
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def entries(lines):
    """Yield (tvg-id, extinf line index, URL line index, URL)."""
    current_id = None
    extinf_index = None
    for index, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("#EXTINF"):
            match = re.search(r'tvg-id="([^"]*)"', line)
            current_id = match.group(1) if match else None
            extinf_index = index
        elif line.startswith(("http://", "https://")) and extinf_index is not None:
            yield current_id, extinf_index, index, line
            current_id = None
            extinf_index = None


if not PLAYLIST.exists():
    raise SystemExit("ERROR: SmartTV.m3u todavía no existe.")

original = PLAYLIST.read_text(encoding="utf-8", errors="replace").splitlines()
local_entries = list(entries(original))
wanted_ids = {item[0] for item in local_entries if item[0]}
print(f"Canales existentes con tvg-id: {len(wanted_ids)}")

# All three source lists must download successfully; otherwise do not partially update.
candidates = {}
for source_url in SOURCE_URLS:
    print(f"Descargando: {source_url}")
    upstream_lines = fetch_text(source_url).splitlines()
    for tvg_id, _, _, url in entries(upstream_lines):
        if tvg_id in wanted_ids:
            candidates.setdefault(tvg_id, []).append(url)

updated_ids = set()
updated_count = 0
for tvg_id, _, url_index, old_url in local_entries:
    if not tvg_id or tvg_id in updated_ids or tvg_id not in candidates:
        continue
    possible_urls = candidates[tvg_id]
    if old_url in possible_urls:
        updated_ids.add(tvg_id)
        continue
    replacement = next(
        (url for url in possible_urls if url != old_url and reachable(url)),
        None,
    )
    if replacement:
        original[url_index] = replacement
        updated_ids.add(tvg_id)
        updated_count += 1

if updated_count:
    PLAYLIST.write_text("\n".join(original) + "\n", encoding="utf-8")
print(f"Canales actualizados: {updated_count}")
print(f"Canales sin coincidencia o sin reemplazo verificable: {len(wanted_ids - updated_ids)}")

# Basic HTTP reachability check; it does not guarantee video playback.
final_lines = PLAYLIST.read_text(encoding="utf-8", errors="replace").splitlines()
urls = [line.strip() for line in final_lines if line.strip().startswith(("http://", "https://"))]
failed = []
print(f"\nComprobando {len(urls)} enlaces...")
for url in urls:
    ok = reachable(url)
    status = "OK" if ok else "REVISAR"
    print(f"{status} | {url}")
    if not ok:
        failed.append(url)

with Path("check-report.md").open("w", encoding="utf-8") as out:
    out.write("# Informe de actualización SmartTV\n\n")
    out.write("- Fuentes: Argentina (ar), México (mx) y Estados Unidos (us) de iptv-org\n")
    for source_url in SOURCE_URLS:
        out.write(f"  - {source_url}\n")
    out.write("- Método: coincidencia exacta por tvg-id\n")
    out.write("- Canales agregados o eliminados: 0\n")
    out.write(f"- Canales actualizados: {updated_count}\n")
    out.write(f"- Enlaces comprobados: {len(urls)}\n")
    out.write(f"- Enlaces para revisar: {len(failed)}\n\n")
    if failed:
        out.write("| Resultado | URL |\n|---|---|\n")
        for url in failed:
            out.write(f"| REVISAR | {url} |\n")
    else:
        out.write("Todos los enlaces respondieron a la comprobación HTTP. Esto no garantiza reproducción en cada aplicación.\n")
