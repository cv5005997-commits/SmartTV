#!/usr/bin/env python3
"""Update existing SmartTV entries from iptv-org's public playlist, then check URLs.

Only exact tvg-id matches are eligible. The script never adds or deletes channels.
If an upstream replacement cannot be reached, the current URL is kept.
"""
import re
import urllib.error
import urllib.request
from pathlib import Path

PLAYLIST = Path("SmartTV.m3u")
SOURCE_URL = "https://iptv-org.github.io/iptv/index.m3u"
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

print("Descargando la lista global de iptv-org (todos los países)...")
upstream_lines = fetch_text(SOURCE_URL).splitlines()
candidates = {}
for tvg_id, _, _, url in entries(upstream_lines):
    if tvg_id in wanted_ids and tvg_id not in candidates:
        candidates[tvg_id] = url

updated_ids = set()
updated_count = 0
checked_candidates = {}
for tvg_id, _, url_index, old_url in local_entries:
    if not tvg_id or tvg_id in updated_ids or tvg_id not in candidates:
        continue
    new_url = candidates[tvg_id]
    if new_url == old_url:
        updated_ids.add(tvg_id)
        continue
    if tvg_id not in checked_candidates:
        checked_candidates[tvg_id] = reachable(new_url)
    if checked_candidates[tvg_id]:
        original[url_index] = new_url
        updated_ids.add(tvg_id)
        updated_count += 1

if updated_count:
    PLAYLIST.write_text("\n".join(original) + "\n", encoding="utf-8")
print(f"Canales actualizados: {updated_count}")
print(f"Canales sin coincidencia o sin reemplazo verificable: {len(wanted_ids - updated_ids)}")

# Check the resulting playlist; this is a basic HTTP check, not a playback guarantee.
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
    out.write(f"- Fuente: [iptv-org, lista global de todos los países]({SOURCE_URL})\n")
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
