#!/usr/bin/env python3
"""Check reachability of stream URLs in SmartTV.m3u without modifying the playlist."""
import re
import urllib.error
import urllib.request
from pathlib import Path

playlist = Path("SmartTV.m3u")
if not playlist.exists():
    raise SystemExit("ERROR: SmartTV.m3u todavía no existe.")

lines = playlist.read_text(encoding="utf-8", errors="replace").splitlines()
urls = []
for line in lines:
    value = line.strip()
    if value.startswith(("http://", "https://")):
        urls.append(value)

if not urls:
    raise SystemExit("ERROR: no se encontraron URLs HTTP/HTTPS en SmartTV.m3u.")

print(f"Comprobando {len(urls)} enlaces\n")
failed = []
for url in urls:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 SmartTV-Playlist-Checker", "Range": "bytes=0-0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            code = response.status
            ok = 200 <= code < 400
    except urllib.error.HTTPError as exc:
        code = exc.code
        ok = False
    except Exception as exc:
        code = type(exc).__name__ + ": " + str(exc)
        ok = False

    label = "OK" if ok else "REVISAR"
    print(f"{label} | {code} | {url}")
    if not ok:
        failed.append((code, url))

summary = Path("check-report.md")
with summary.open("w", encoding="utf-8") as out:
    out.write("# Informe de comprobación SmartTV\n\n")
    out.write(f"- Enlaces comprobados: {len(urls)}\n")
    out.write(f"- Enlaces para revisar: {len(failed)}\n\n")
    if failed:
        out.write("| Resultado | URL |\n|---|---|\n")
        for code, url in failed:
            out.write(f"| {str(code).replace('|', '/')} | {url} |\n")
    else:
        out.write("Todos los enlaces respondieron en esta comprobación. Esto no garantiza que el reproductor pueda decodificar el vídeo.\n")

print(f"\nResultado: {len(failed)} de {len(urls)} enlaces requieren revisión.")
