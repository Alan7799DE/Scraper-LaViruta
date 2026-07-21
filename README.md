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

- **Fuente de verdad = el scrapeo del árbol de categorías.** No se usa el
  `sitemap.xml` (no se confía en su completitud ni en cómo se genera).
- **Recorrido robusto:** iterar `page=N` hasta que una página no devuelva
  productos. El botón «siguiente» no es confiable como señal de fin.
- Un producto que no esté en ninguna categoría **no aparece** en el listado
  (no es alcanzable por navegación). Es intencional.

## Uso

Requiere **Python 3.8+** y solo biblioteca estándar (no hay que instalar nada).

```bash
python3 scripts/relevar_catalogo.py
```

### Salidas (siempre en la carpeta del proyecto, sin importar desde dónde se ejecute)

| Archivo | Contenido |
|---|---|
| `productos.csv` | 1 fila por SKU: `sku, nombre, categorias, subcategorias, n_clasificaciones, estado` |
| `productos_clasificaciones.csv` | Formato largo: 1 fila por `(SKU, categoría, subcategoría, sub-subcategoría, ruta)` |
| `productos.json` | Detalle completo por SKU |

Los CSV se escriben en `utf-8-sig` para que Excel muestre bien los acentos.

### Configuración

Editable al principio de [`scripts/relevar_catalogo.py`](scripts/relevar_catalogo.py):
`PER_PAGE`, `WORKERS`, `MAX_PAGES`, `TIMEOUT`, `RETRIES`, `PAUSE`.

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
