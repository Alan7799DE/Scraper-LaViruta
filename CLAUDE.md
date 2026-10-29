# Scraper LaViruta

Scraper para el e-commerce **Maderas La Viruta** — https://laviruta.com/.

## Objetivo

Relevar el catálogo completo de La Viruta para **auditar y mejorar las
descripciones de los productos**. Muchas fichas tienen una descripción pobre o
vacía (en la práctica, gran parte solo repite el nombre). El scraper arma el
dataset completo — SKU, nombre, clasificación y descripción actual — para
revisarlas y reescribirlas de forma sistemática.

## Estado

- **Fase:** scraper de índice funcionando (`scripts/relevar_catalogo.py`),
  con extracción de descripciones.
- Última corrida completa: ~1.933 productos → ~811 con descripción real,
  ~1.090 que solo repiten el nombre, ~25 sin descripción.
- Pendientes conocidos:
  - `fetch` solo captura `URLError`/`HTTPError`: un timeout o reset durante la
    lectura (`TimeoutError`, `ConnectionResetError`) no se reintenta y aborta
    la corrida sin escribir salidas.
  - Si una página falla tras los reintentos, `fetch` devuelve `""` y
    `recorrer_ruta` lo toma como fin de paginación → datos truncados en
    silencio (solo queda un aviso en stderr).
  - Se reintentan errores 404 (no tiene sentido).

## Sitio objetivo

- URL: https://laviruta.com/
- Plataforma: **Laravel / PHP 8.2** (Apache). Usa carrito y sesión de compra
  (`lavirutaonlineshop_session`, token XSRF); para leer el catálogo no hace
  falta sesión.
- **TLS:** el certificado tiene la **cadena incompleta** (falta el intermedio).
  El script desactiva la verificación TLS por eso (es el servidor propio).
- Árbol: ~21 categorías · ~157 subcategorías · algunas rutas de nivel 3.
- Listado: `shop/{categoria}[/{subcategoria}]?per_page=N&page=N`
  (`per_page` acepta 12 / 24 / 36). Paginación clásica, sin AJAX ni scroll
  infinito. El botón «siguiente» **no** es señal confiable de fin: se itera
  hasta que una página no trae productos.
- `/shop` sin filtro lista **todos** los productos publicados (con o sin
  categoría) → es la fuente maestra de enumeración.
- SKU = path tras `/product/`. **Puede contener barras** (`CORNIZ7/1`,
  `ESCUAKC/A`).
- Nombre = atributo `title=` de la tarjeta (`<a class="product-image">`).
- Descripción = solapa `#product_tabs_description` → `<div class="std">` en la
  ficha. Si no hay descripción real, la solapa muestra el nombre.
- Alias: el sitio expone slugs de 6 letras (`abertu` == `aberturas`) con los
  mismos productos; se deduplican agrupando rutas por conjunto de SKU.
- El `sitemap.xml` está incompleto: **no se usa**.

## Stack

- **Python 3.8+, solo biblioteca estándar** (`urllib`, `re`, `html`,
  `concurrent.futures`, `csv`, `json`). Sin dependencias.
- Parsing con regex / búsqueda de strings (sin BeautifulSoup).

## Uso

```bash
python3 scripts/relevar_catalogo.py
```

Configuración al inicio del script: `PER_PAGE`, `WORKERS`, `MAX_PAGES`,
`TIMEOUT`, `RETRIES`, `PAUSE`, `TRAER_DESCRIPCION` (en `False` omite abrir las
fichas y es mucho más rápido).

Salidas (siempre en la raíz del proyecto, ignoradas por git, CSV en
`utf-8-sig` para Excel):

- `productos.csv` — 1 fila por SKU: `sku, nombre, categorias, subcategorias,
  n_clasificaciones, estado, descripcion`
- `productos_clasificaciones.csv` — formato largo, 1 fila por (SKU, ruta)
- `productos.json` — detalle completo por SKU

`estado`: `clasificado` (tiene subcategoría) · `suelto` (solo categoría) ·
`sin_categoria` (aparece en `/shop` pero en ninguna categoría).

## Estructura

```
scripts/relevar_catalogo.py   # scraper de índice + descripciones
README.md                     # documentación (en inglés)
CLAUDE.md                     # contexto del proyecto (este archivo)
.claude/                      # skills, hooks, settings
```

## Convenciones

- Este proyecto usa las **skills de `.claude/skills/`** (superpowers). El hook
  `session-start` recuerda invocarlas proactivamente: ante cualquier tarea que
  encaje con una skill, usarla con la herramienta Skill antes de actuar.
- Código versionado en GitHub (rama `main`); los cambios entran por Pull
  Request desde una rama `feature/…`, `fix/…` o `docs/…`.
- Mensajes de commit y comentarios del código en español; el README está en
  inglés.
- Scraping responsable: aunque es el servidor propio, mantener paralelismo
  moderado y no sobrecargarlo.
