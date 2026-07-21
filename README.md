# La Viruta Scraper

A catalog scraper for **Maderas La Viruta** — <https://laviruta.com/>.

It walks the online store and produces a complete list of products with their
**SKU**, **name**, **category/subcategory classification**, and **description**.

## Why

The goal is to **audit and improve the product descriptions**. Many products in
the store have weak or missing descriptions (in practice, a large share only
repeat the product name). To fix that at scale you first need the full picture:
every SKU, its current name, its current description, and where it sits in the
catalog. This scraper builds exactly that dataset so the descriptions can be
reviewed and rewritten systematically.

## What it extracts

For every published product:

| Field | Source |
|---|---|
| `sku` | Path after `/product/` in the product URL |
| `nombre` (name) | `title=` attribute of the product card |
| `categorias` / `subcategorias` | The category/subcategory routes the product appears under |
| `descripcion` (description) | Text of the "Descripción del Producto" tab on the product page |
| `estado` | `clasificado` / `suelto` (in a category, no subcategory) / `sin_categoria` |

## How the site works (as observed)

| Aspect | Detail |
|---|---|
| Platform | Laravel / PHP 8.2 on Apache |
| Catalog tree | ~21 categories · ~157 subcategories · a few level-3 routes |
| Pagination | Classic numbered pages (1, 2, 3, `»`). **No** infinite scroll, **no** AJAX |
| Listing URL | `shop/{category}[/{subcategory}]?per_page=N&page=N` (`per_page` accepts 12 / 24 / 36) |
| SKU | Path after `/product/`. **May contain slashes** (e.g. `CORNIZ7/1`, `ESCUAKC/A`) — the site reports it that way in the "Código" field |
| Name | `title=` attribute of the product card (no need to open the page) |
| Description | `#product_tabs_description` tab → `<div class="std">` on the product page |

## Scraping strategy

- **Source of truth = the scrape itself.** The `sitemap.xml` is *not* used (it is
  incomplete and its generation can't be relied on).
- **Enumeration (master list):** the general `/shop` listing (no category filter)
  lists **every** published product, whether or not it has a category. This is
  what guarantees completeness.
- **Classification:** categories/subcategories are crawled only to *label* each
  SKU. A product that appears in `/shop` but under no category is marked
  `sin_categoria` (instead of being lost).
- **Robust pagination:** iterate `page=N` until a page returns no products. The
  «next» button is not a reliable end-of-list signal.
- **Alias de-duplication:** the site exposes internal 6-letter aliases (e.g.
  `abertu` == `aberturas`) that return the same products with a differently-cased
  label. Routes are grouped by their SKU set and only the canonical one is kept,
  so rows and labels aren't duplicated. Real categories without a twin (e.g.
  `Placas`, `Herramientas`) are preserved.

## Usage

Requires **Python 3.8+** and the standard library only — nothing to install.

```bash
python3 scripts/relevar_catalogo.py
```

A full run opens every product page for the descriptions and takes a few minutes.
Set `TRAER_DESCRIPCION = False` to skip descriptions for a much faster run.

### Outputs (written to the project folder, regardless of where you run it)

| File | Contents |
|---|---|
| `productos.csv` | One row per SKU: `sku, nombre, categorias, subcategorias, n_clasificaciones, estado, descripcion` |
| `productos_clasificaciones.csv` | Long format: one row per `(SKU, category, subcategory, sub-subcategory, route)` |
| `productos.json` | Full detail per SKU |

CSV files are written as `utf-8-sig` so Excel renders accents correctly.

### Configuration

At the top of [`scripts/relevar_catalogo.py`](scripts/relevar_catalogo.py):
`PER_PAGE`, `WORKERS`, `MAX_PAGES`, `TIMEOUT`, `RETRIES`, `PAUSE`,
`TRAER_DESCRIPCION`.

> **TLS note:** the `laviruta.com` certificate ships an incomplete chain (missing
> intermediate). The script disables TLS verification for that reason; it's
> acceptable here because it targets the store's own server.

## Description audit — what the data shows

In a recent full run (~1,933 products), the descriptions broke down roughly as:

- **~811** products with a **real** description (different from the name).
- **~1,090** products whose description **only repeats the product name** — these
  are the primary targets for rewriting.
- **~25** with no description at all.

Products in the last two groups are trivial to filter (description empty, or
equal to `nombre`), which makes `productos.csv` a ready-made worklist for the
description review.

## Project structure

```
.
├── README.md
├── CLAUDE.md                     # Project context and conventions
├── scripts/
│   └── relevar_catalogo.py       # Catalog index scraper
└── .claude/                      # Claude Code configuration (skills, hooks)
```

## Conventions

- Code is versioned on GitHub (`main` branch); changes go through Pull Requests.
- Scraped outputs (`productos.*`) are git-ignored.
- Responsible scraping: even though it targets the store's own server with no
  request limit, the code stays tidy and avoids excessive parallelism.
