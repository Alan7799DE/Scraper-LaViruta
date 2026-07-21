#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relevar_catalogo.py — Scraper de índice para https://laviruta.com/shop

Recorre TODO el árbol de categorías y subcategorías del e-commerce y arma un
listado de productos con: SKU, nombre y su clasificación (categoría /
subcategoría / sub-subcategoría).

FUENTE DE VERDAD: lo que se scrapea recorriendo el árbol de categorías.
NO usa el sitemap.xml (no se confía en él).

Notas de diseño:
  - Un producto que NO esté en ninguna categoría no aparecerá en el listado:
    es esperable, porque solo consideramos lo alcanzable por navegación.
  - El SKU es el último segmento de la URL /product/{SKU}.
  - El nombre sale del atributo title= de la tarjeta del listado (no hace falta
    abrir cada ficha).
  - La clasificación de cada producto = las rutas /shop/... bajo las que aparece.
  - Paginación: ?per_page=36&page=N, iterando hasta que una página no traiga
    productos (el botón "siguiente" NO es confiable como señal de fin).

Requisitos: Python 3.8+ y biblioteca estándar. NO hay que instalar nada.

Uso:
    python3 relevar_catalogo.py

Salidas (en el directorio actual):
    productos.csv                  -> 1 fila por SKU (clasificación agregada)
    productos_clasificaciones.csv  -> formato largo: 1 fila por (SKU, clasificación)
    productos.json                 -> detalle completo por SKU
"""

import csv
import html
import json
import os
import re
import ssl
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Carpeta del proyecto (raíz), independiente de desde dónde se ejecute el
# script. El script vive en scripts/, así que la raíz es su carpeta padre.
# Ahí se dejan siempre los archivos de salida.
DIR_SALIDA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
BASE = "https://laviruta.com"
PER_PAGE = 36            # 12 | 24 | 36 (36 = menos requests)
WORKERS = 8             # hilos en paralelo (es servidor propio: se puede subir)
MAX_PAGES = 100         # corte de seguridad por categoría
TIMEOUT = 30            # segundos por request
RETRIES = 3             # reintentos ante error de red
PAUSE = 0.0            # pausa entre requests dentro de un mismo hilo (seg)
USER_AGENT = "LaVirutaCatalogScraper/1.0 (relevamiento interno)"

# El certificado de laviruta.com tiene la cadena incompleta (falta el
# intermedio). Como es el servidor propio, desactivamos la verificación TLS.
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def fetch(url):
    """Descarga una URL y devuelve el HTML como str (con reintentos)."""
    last_err = None
    for intento in range(1, RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, HTTPError) as e:
            last_err = e
            time.sleep(1.0 * intento)
    print(f"  [!] Falló {url}: {last_err}", file=sys.stderr)
    return ""


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
# Enlaces del menú a categorías/subcategorías, con su etiqueta (nombre lindo).
RE_SHOP_LINK = re.compile(
    r'<a\b[^>]*href="(?:' + re.escape(BASE) + r')?/shop/([a-z0-9/\-]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
# Anclas de tarjeta de producto en el listado: <a ... class="product-image">
RE_PRODUCT_ANCHOR = re.compile(r'<a\b[^>]*class="product-image"[^>]*>', re.I)
RE_SKU_IN_HREF = re.compile(r'/product/([^"/?#]+)', re.I)
RE_TITLE_ATTR = re.compile(r'title="([^"]*)"', re.I)
RE_TAGS = re.compile(r"<[^>]+>")


def limpiar(texto):
    """Quita tags HTML, decodifica entidades y normaliza espacios."""
    texto = RE_TAGS.sub("", texto)
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def descubrir_arbol():
    """
    Devuelve dict {ruta: etiqueta} con todas las categorías y subcategorías.
    'ruta' es relativa a /shop/ (ej: 'maderas', 'maderas/machimbres').
    Descubre desde el menú de /shop y refuerza visitando cada categoría nivel 1.
    """
    print("→ Descubriendo el árbol de categorías…")
    etiquetas = {}

    def registrar(htmltext):
        for ruta, inner in RE_SHOP_LINK.findall(htmltext):
            etiqueta = limpiar(inner)
            if not etiqueta:
                continue  # descarta los slugs truncados del menú rápido (sin texto)
            ruta = ruta.rstrip("/")
            if ruta and ruta not in etiquetas:
                etiquetas[ruta] = etiqueta

    registrar(fetch(f"{BASE}/shop"))

    # Refuerzo: cada categoría de nivel 1 puede listar subcategorías propias.
    nivel1 = [r for r in list(etiquetas) if "/" not in r]
    for cat in nivel1:
        registrar(fetch(f"{BASE}/shop/{cat}"))

    print(f"  {len(etiquetas)} rutas (categorías + subcategorías) encontradas.")
    return etiquetas


def productos_en_pagina(htmltext):
    """Extrae [(sku, nombre)] de una página de listado."""
    out = []
    for tag in RE_PRODUCT_ANCHOR.findall(htmltext):
        msku = RE_SKU_IN_HREF.search(tag)
        if not msku:
            continue
        sku = msku.group(1)
        mtit = RE_TITLE_ATTR.search(tag)
        nombre = limpiar(mtit.group(1)) if mtit else ""
        out.append((sku, nombre))
    return out


def recorrer_ruta(ruta):
    """
    Recorre una categoría/subcategoría paginando hasta agotarla.
    Devuelve (ruta, [(sku, nombre), ...]) sin deduplicar.
    """
    encontrados = []
    page = 1
    while page <= MAX_PAGES:
        url = f"{BASE}/shop/{ruta}?per_page={PER_PAGE}&page={page}"
        prods = productos_en_pagina(fetch(url))
        if not prods:
            break
        encontrados.extend(prods)
        page += 1
        if PAUSE:
            time.sleep(PAUSE)
    return ruta, encontrados


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #
def main():
    etiquetas = descubrir_arbol()
    rutas = sorted(etiquetas.keys())
    if not rutas:
        print("No se descubrió ninguna categoría. Abortando.", file=sys.stderr)
        sys.exit(1)

    # productos[sku] = {"nombre": str, "rutas": set()}
    productos = {}
    lock = threading.Lock()

    print(f"→ Recorriendo {len(rutas)} rutas con {WORKERS} hilos "
          f"(per_page={PER_PAGE})…")
    completadas = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futuros = {ex.submit(recorrer_ruta, r): r for r in rutas}
        for fut in as_completed(futuros):
            ruta, prods = fut.result()
            with lock:
                for sku, nombre in prods:
                    reg = productos.setdefault(sku, {"nombre": "", "rutas": set()})
                    if nombre and not reg["nombre"]:
                        reg["nombre"] = nombre
                    reg["rutas"].add(ruta)
            completadas += 1
            print(f"  [{completadas}/{len(rutas)}] {ruta}: {len(prods)} productos")

    print(f"→ Total de SKU únicos: {len(productos)}")

    # ---- Clasificación por producto ---------------------------------------- #
    def nombre_cat(slug):
        return etiquetas.get(slug, slug)

    def desglosar(ruta):
        """'aberturas/puertas/mdf' -> (cat, subcat, subsub) con nombres lindos."""
        partes = ruta.split("/")
        cat = nombre_cat(partes[0])
        sub = nombre_cat("/".join(partes[:2])) if len(partes) >= 2 else ""
        subsub = nombre_cat("/".join(partes[:3])) if len(partes) >= 3 else ""
        return cat, sub, subsub

    filas_wide = []   # 1 por SKU
    filas_long = []   # 1 por (SKU, clasificación)
    detalle = {}

    for sku in sorted(productos):
        reg = productos[sku]
        nombre = reg["nombre"]
        rutas_sku = sorted(reg["rutas"])

        # Agrupar por categoría de nivel 1 para detectar "sueltos".
        por_cat = {}
        for r in rutas_sku:
            por_cat.setdefault(r.split("/")[0], []).append(r)

        clasifs = []  # rutas "más profundas" que representan la clasificación
        for cat, rs in por_cat.items():
            subs = [r for r in rs if "/" in r]
            clasifs.extend(subs if subs else [cat])

        categorias = sorted({nombre_cat(r.split("/")[0]) for r in clasifs})
        subcats = sorted({desglosar(r)[1] for r in clasifs if "/" in r})
        estado = "clasificado" if subcats else "suelto"

        filas_wide.append({
            "sku": sku,
            "nombre": nombre,
            "categorias": " | ".join(categorias),
            "subcategorias": " | ".join(subcats),
            "n_clasificaciones": len(clasifs),
            "estado": estado,
        })

        for r in clasifs:
            cat, sub, subsub = desglosar(r)
            filas_long.append({
                "sku": sku,
                "nombre": nombre,
                "categoria": cat,
                "subcategoria": sub,
                "sub_subcategoria": subsub,
                "ruta": r,
                "estado": "suelto" if "/" not in r else "clasificado",
            })

        detalle[sku] = {
            "nombre": nombre,
            "categorias": categorias,
            "subcategorias": subcats,
            "rutas": clasifs,
            "estado": estado,
        }

    # ---- Escribir salidas (siempre en la carpeta del proyecto) ------------- #
    ruta_wide = os.path.join(DIR_SALIDA, "productos.csv")
    ruta_long = os.path.join(DIR_SALIDA, "productos_clasificaciones.csv")
    ruta_json = os.path.join(DIR_SALIDA, "productos.json")

    with open(ruta_wide, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "sku", "nombre", "categorias", "subcategorias",
            "n_clasificaciones", "estado"])
        w.writeheader()
        w.writerows(filas_wide)

    with open(ruta_long, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "sku", "nombre", "categoria", "subcategoria",
            "sub_subcategoria", "ruta", "estado"])
        w.writeheader()
        w.writerows(filas_long)

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(detalle, f, ensure_ascii=False, indent=2)

    # ---- Resumen ----------------------------------------------------------- #
    sueltos = sum(1 for d in detalle.values() if d["estado"] == "suelto")
    print("\n=========== RESUMEN ===========")
    print(f"SKU únicos             : {len(detalle)}")
    print(f"Con subcategoría       : {len(detalle) - sueltos}")
    print(f"Sueltos (solo categoría): {sueltos}")
    print(f"Categorías nivel 1     : {len([r for r in rutas if '/' not in r])}")
    print(f"Subcategorías          : {len([r for r in rutas if '/' in r])}")
    print(f"\nArchivos generados en: {DIR_SALIDA}")
    print("  - productos.csv")
    print("  - productos_clasificaciones.csv")
    print("  - productos.json")


if __name__ == "__main__":
    main()
