# Scraper La Viruta

Scraper del catálogo online de **Maderas La Viruta** — <https://laviruta.com/>.

Extrae, recorriendo el árbol de categorías del e-commerce, un listado de
productos con su **SKU**, **nombre** y **clasificación** (categoría /
subcategoría / sub-subcategoría).

## Estado

- **Fase:** relevamiento del catálogo.
- **Script disponible:** [`scripts/relevar_catalogo.py`](scripts/relevar_catalogo.py)
  — genera el índice completo de productos y su clasificación.

## Cómo funciona el sitio (relevado)

| Aspecto | Detalle |
|---|---|
| Plataforma | Laravel / PHP 8.2 sobre Apache |
| Árbol | 21 categorías · 157 subcategorías · 3 rutas de nivel 3 (`aberturas/puertas/*`) |
| Paginación | Clásica (botones 1, 2, 3, `»`). **No** hay scroll infinito ni AJAX |
| URL de listado | `shop/{categoria}[/{subcategoria}]?per_page=N&page=N` (`per_page` acepta 12 / 24 / 36) |
| SKU | Último segmento de la URL de producto: `laviruta.com/product/{SKU}` |
| Nombre | Atributo `title=` de la tarjeta del listado (no hace falta abrir la ficha) |

### Criterios de scraping

- **Fuente de verdad = el scrapeo del sitio.** No se usa el `sitemap.xml`
  (no se confía en su completitud ni en cómo se genera; además está incompleto).
- **Enumeración (maestra):** el listado general `/shop` (sin filtro de
  categoría) lista **todos** los productos publicados, tengan o no categoría.
- **Clasificación:** se recorren además las categorías/subcategorías para
  asignarle a cada SKU su categoría/subcategoría.
- Un producto presente en `/shop` pero en ninguna categoría queda con estado
  **`sin_categoria`** (no se pierde).
- **Recorrido robusto:** iterar `page=N` hasta que una página no devuelva
  productos. El botón «siguiente» no es confiable como señal de fin.
- **Dedup de alias:** el sitio expone alias internos de 6 letras (p. ej.
  `abertu` == `aberturas`) que devuelven el mismo contenido con otra etiqueta.
  Se agrupan las rutas por su conjunto de SKU y se conserva la canónica, así no
  se duplican filas ni etiquetas. Las rutas sin gemelo (categorías reales que no
  están en el menú, como `Placas` o `Herramientas`) se conservan.

## Uso

Requiere **Python 3.8+** y solo biblioteca estándar (no hay que instalar nada).

```bash
python3 scripts/relevar_catalogo.py
```

### Salidas (siempre en la carpeta del proyecto, sin importar desde dónde se ejecute)

| Archivo | Contenido |
|---|---|
| `productos.csv` | 1 fila por SKU: `sku, nombre, categorias, subcategorias, n_clasificaciones, estado, descripcion` |
| `productos_clasificaciones.csv` | Formato largo: 1 fila por `(SKU, categoría, subcategoría, sub-subcategoría, ruta)` |
| `productos.json` | Detalle completo por SKU |

La columna **`descripcion`** sale de abrir la ficha `/product/{SKU}` y leer la
solapa «Descripción del Producto». Cuando el producto no tiene descripción real,
esa solapa muestra el nombre (se deja tal cual). Se puede desactivar con
`TRAER_DESCRIPCION = False` (bastante más rápido, no abre las fichas).

Los CSV se escriben en `utf-8-sig` para que Excel muestre bien los acentos.

### Configuración

Editable al principio de [`scripts/relevar_catalogo.py`](scripts/relevar_catalogo.py):
`PER_PAGE`, `WORKERS`, `MAX_PAGES`, `TIMEOUT`, `RETRIES`, `PAUSE`,
`TRAER_DESCRIPCION`.

> **Nota TLS:** el certificado de `laviruta.com` tiene la cadena incompleta
> (falta el intermedio). El script desactiva la verificación TLS por ese
> motivo; es aceptable porque es el servidor propio.

## Estructura

```
.
├── README.md
├── CLAUDE.md                     # Contexto y convenciones del proyecto
├── scripts/
│   └── relevar_catalogo.py       # Scraper de índice del catálogo
└── .claude/                      # Configuración de Claude Code (skills, hooks)
```

## Convenciones

- Código versionado en GitHub (rama `main`), cambios vía Pull Request.
- Scraping responsable: aunque es el servidor propio y no hay límite de
  requests, mantener el código prolijo y sin paralelismo desmedido.
