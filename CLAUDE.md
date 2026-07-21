# Scraper LaViruta

Scraper para el e-commerce **Maderas La Viruta** — https://laviruta.com/.

## Objetivo

Extraer datos del catálogo online de La Viruta (maderas, pisos, placas y demás
productos). El alcance concreto (qué campos, con qué frecuencia, formato de
salida) se irá detallando con el usuario a lo largo del desarrollo.

## Estado

- **Fase:** inicial — setup del repo y del entorno de trabajo.
- **Alcance del scraping:** por definir (el usuario dará indicaciones sobre qué
  datos buscamos y cómo extraerlos).

## Sitio objetivo

- URL: https://laviruta.com/
- Plataforma: e-commerce en **Laravel / PHP 8.2** (Apache). Usa carrito y
  sesión de compra (`lavirutaonlineshop_session`, token XSRF).
- Nota técnica: el certificado SSL tiene la **cadena incompleta** (falta el
  intermedio). El navegador la abre bien, pero clientes HTTP estrictos pueden
  fallar la verificación TLS — tenerlo en cuenta al elegir librería/cliente.
- Secciones observadas en la home: "Pisos de Madera", "Destacados del Mes".

## Stack

**Por definir.** Todavía no se eligió lenguaje ni librerías. Se decidirá junto
con el usuario según los requisitos del scraping. Cuando se defina, actualizar
esta sección y `.claude/launch.json`.

## Convenciones

- Este proyecto usa las **skills de `.claude/skills/`** (superpowers). El hook
  `session-start` recuerda invocarlas proactivamente: ante cualquier tarea que
  encaje con una skill, usarla con la herramienta Skill antes de actuar.
- El código se versiona en GitHub (rama `main`).
- Scraping responsable: respetar el sitio (rate limiting, no sobrecargar el
  servidor), y revisar `robots.txt` / términos antes de escalar volumen.
