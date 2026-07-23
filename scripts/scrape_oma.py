#!/usr/bin/env python3
"""
Scraper de enunciados de OMA (Olimpíada Matemática Argentina) — Nivel 2.

⚠️  IMPORTANTE
El entorno donde se generó esta app tiene bloqueado el acceso a oma.org.ar,
así que este script NO pudo ejecutarse/validarse contra el sitio real. Está
pensado para que lo corras vos en una red con acceso a internet abierto.

La estructura del sitio de OMA puede cambiar; por eso el parseo está aislado en
`parse_certamen()` y es fácil de ajustar. El script:

  1. Recorre el índice de enunciados.
  2. Detecta certámenes de las instancias que nos interesan (Intercolegial / Zonal).
  3. Extrae los problemas de Nivel 2 de cada uno.
  4. Escribe `public/oma-nivel2.json` con el formato que importa la app.

Uso:
    pip install requests beautifulsoup4
    python scripts/scrape_oma.py                 # scrapea y guarda public/oma-nivel2.json
    python scripts/scrape_oma.py --list          # solo lista los enlaces detectados
    python scripts/scrape_oma.py --out data.json # cambia el archivo de salida

Formato de salida (array de problemas):
    {
      "id": "Zonal-2020-N2-P1",
      "anio": 2020,
      "instancia": "Zonal",           # "Intercolegial" | "Zonal"
      "nivel": 2,
      "numero": 1,
      "enunciado": "…",
      "fuente": "https://www.oma.org.ar/enunciados/…"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(
        "Faltan dependencias. Instalá con:\n    pip install requests beautifulsoup4"
    )

BASE = "https://www.oma.org.ar/enunciados/"
INDEX = urljoin(BASE, "index.htm")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oma-practica-scraper/1.0)"}

# Instancias que le importan a la app.
INSTANCIAS = ("Intercolegial", "Zonal")


@dataclass
class Problema:
    id: str
    anio: int
    instancia: str
    nivel: int
    numero: int
    enunciado: str
    fuente: str


def get(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "latin-1"
    return resp.text


def detectar_instancia(texto: str) -> str | None:
    t = texto.lower()
    if "intercolegial" in t:
        return "Intercolegial"
    if "zonal" in t:
        return "Zonal"
    return None


def detectar_anio(texto: str) -> int | None:
    m = re.search(r"(19|20)\d{2}", texto)
    return int(m.group(0)) if m else None


def descubrir_certamenes(index_html: str) -> list[dict]:
    """Devuelve [{url, instancia, anio, titulo}] a partir del índice."""
    soup = BeautifulSoup(index_html, "html.parser")
    encontrados: list[dict] = []
    for a in soup.find_all("a", href=True):
        titulo = a.get_text(" ", strip=True)
        instancia = detectar_instancia(titulo) or detectar_instancia(a["href"])
        if not instancia:
            continue
        anio = detectar_anio(titulo) or detectar_anio(a["href"])
        encontrados.append(
            {
                "url": urljoin(INDEX, a["href"]),
                "instancia": instancia,
                "anio": anio,
                "titulo": titulo,
            }
        )
    return encontrados


def parse_certamen(html: str, instancia: str, anio: int, fuente: str) -> list[Problema]:
    """
    Extrae los problemas de Nivel 2 de la página de un certamen.

    ⚠️ AJUSTAR según el HTML real de OMA. Heurística por defecto: busca una
    sección cuyo encabezado mencione "Nivel 2" y toma los párrafos numerados
    (1., 2., …) como enunciados. Si OMA publica PDFs, habrá que descargarlos y
    extraer el texto (por ejemplo con pdfplumber) en vez de esto.
    """
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text("\n", strip=True)

    # Aislar el bloque de "Nivel 2" hasta el próximo "Nivel N".
    m = re.search(r"Nivel\s*2\b(.*?)(?:Nivel\s*[13]\b|$)", texto, re.S | re.I)
    bloque = m.group(1) if m else texto

    problemas: list[Problema] = []
    # Enunciados numerados "1. ...", "2) ...", "Problema 1 ..."
    partes = re.split(r"(?m)^\s*(?:Problema\s*)?(\d{1,2})[\.\)]\s+", bloque)
    # partes = ['', '1', 'texto1', '2', 'texto2', ...]
    for i in range(1, len(partes) - 1, 2):
        try:
            numero = int(partes[i])
        except ValueError:
            continue
        enunciado = re.sub(r"\s+\n", "\n", partes[i + 1].strip())
        enunciado = re.sub(r"\n{2,}", "\n", enunciado)[:2000].strip()
        if not enunciado:
            continue
        problemas.append(
            Problema(
                id=f"{instancia}-{anio}-N2-P{numero}",
                anio=anio,
                instancia=instancia,
                nivel=2,
                numero=numero,
                enunciado=enunciado,
                fuente=fuente,
            )
        )
    return problemas


def main() -> int:
    ap = argparse.ArgumentParser(description="Scraper de enunciados OMA Nivel 2")
    ap.add_argument("--out", default="public/oma-nivel2.json", help="Archivo de salida")
    ap.add_argument("--list", action="store_true", help="Solo listar certámenes detectados")
    ap.add_argument("--delay", type=float, default=1.0, help="Pausa entre requests (s)")
    args = ap.parse_args()

    print(f"→ Descargando índice: {INDEX}")
    index_html = get(INDEX)
    certamenes = descubrir_certamenes(index_html)
    certamenes = [c for c in certamenes if c["instancia"] in INSTANCIAS and c["anio"]]

    print(f"→ {len(certamenes)} certámenes candidatos (Intercolegial/Zonal).")
    if args.list:
        for c in certamenes:
            print(f"  [{c['instancia']:13} {c['anio']}] {c['url']}")
        return 0

    todos: list[Problema] = []
    for c in certamenes:
        try:
            html = get(c["url"])
            probs = parse_certamen(html, c["instancia"], c["anio"], c["url"])
            print(f"  {c['instancia']} {c['anio']}: {len(probs)} problemas")
            todos.extend(probs)
            time.sleep(args.delay)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️  Error en {c['url']}: {e}", file=sys.stderr)

    # Deduplicar por id.
    unicos = {p.id: p for p in todos}
    salida = [asdict(p) for p in unicos.values()]
    salida.sort(key=lambda p: (p["instancia"], p["anio"], p["numero"]))

    import os

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(salida)} problemas escritos en {args.out}")
    print("  Importalos en la app: pestaña 'Datos' → Subir archivo .json")
    if not salida:
        print(
            "\n⚠️  No se extrajo ningún problema. Es muy probable que haya que ajustar\n"
            "   parse_certamen() al HTML real (o extraer desde PDFs). Corré con --list\n"
            "   para ver los enlaces y revisá la estructura de una página de certamen."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
