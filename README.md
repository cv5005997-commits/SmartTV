# SmartTV

Repositorio independiente para la lista de canales IPTV.

## Enlace corto de la lista

**[Abrir SmartTV.m3u](https://is.gd/Yal5Ft)**

Copiá ese enlace en Televizo u otro reproductor IPTV.

- `SmartTV.m3u`: lista de reproducción.
- `scripts/check_playlist.py`: comprobación periódica de enlaces HTTP/HTTPS.
- GitHub Actions ejecuta la comprobación cada 6 horas y también manualmente.

La comprobación detecta y reporta enlaces que no responden; no sustituye automáticamente una URL caída por otra. Para reparar un canal hace falta una URL alternativa válida y verificada.

**URL directa de respaldo:**  
`https://raw.githubusercontent.com/cv5005997-commits/SmartTV/main/SmartTV.m3u`
