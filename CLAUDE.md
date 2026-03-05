# CURIOSIDADES — Buscador de Empleo Personalizado para Freddy Huaylla

## Propósito

Script Python que automatiza la búsqueda de ofertas de trabajo remotas en LATAM
ajustadas al perfil real de Freddy. El objetivo es iterar hasta tener un scraper
que devuelva resultados de alta calidad cada vez que se ejecuta.

---

## Perfil del desarrollador

**Freddy Huaylla** — Fullstack Developer, Arica CL
Stack en orden de fortaleza:

1. **JavaScript/TypeScript** (principal) → React, Next.js, Node.js, NestJS, Express
2. **Python** (segunda habilidad fuerte) → Django, FastAPI
3. **Flutter** (mobile, importante pero no el core)

Nivel de mercado: **Junior avanzado / Semi Senior** (muy pocas postulaciones Senior)
Modalidad buscada: **100% remoto**, preferentemente con horario LATAM.
Idioma preferido en ofertas: **español**, aunque inglés también es aceptable.

---

## Flujo de trabajo

```
1. Editar job1/jobspy_search.py  →  ajustar queries, pesos, filtros, países
2. pipenv run job1                →  ejecutar el script
3. Revisar .md generado           →  resumen legible agrupado por site con links
4. Analizar .csv si se requiere   →  datos completos para iterar con IA
5. Iterar sobre configuración     →  volver al paso 1
```

> ⚠️ NO ejecutar el script sin autorización del usuario.
> ⚠️ Esperar al menos 12-24h entre ejecuciones para evitar soft-ban de LinkedIn.
> ⚠️ Si se modifica el script, SIEMPRE actualizar este CLAUDE.md (arquitectura, versión, aprendizajes) en el mismo cambio.

---

## Estructura de archivos

```
job-radar-latam/
├── CLAUDE.md                            ← este archivo (contexto para IA)
├── Pipfile                              ← dependencias (pipenv run job1)
├── Pipfile.lock                         ← lock file (trackeado, Railway lo necesita)
├── README.md                            ← instrucciones de uso
├── railway.toml                         ← config Railway (Nixpacks, restart policy)
└── job1/
    ├── jobspy_search.py                 ← entry point: main() orquesta el flujo (~70 líneas)
    ├── config.py                        ← configuración: queries, pesos, filtros, empresas excluidas
    ├── helpers.py                       ← funciones: scraping, filtros, scoring, export, email
    ├── manual_sources.json              ← URLs manuales de portales no soportados
    └── YYYYMMDD_HHMM/                  ← carpeta por run
        ├── results.csv                  ← datos completos para análisis por IA
        ├── results.md                   ← resumen legible con links (para Freddy)
        └── discarded.md                 ← descartados para revisión manual
```

---

## Arquitectura del script

### Sitios usados (y por qué)

| Sitio       | Cómo se usa          | Razón                                      |
|-------------|----------------------|--------------------------------------------|
| LinkedIn    | `is_remote=True`     | Filtra remoto a nivel API nativo            |
| Indeed      | `hours_old=168`      | API prohíbe usar is_remote + hours_old juntos |
| Google      | ❌ eliminado          | Retorna 0 resultados para LATAM            |
| ZipRecruiter| ❌ eliminado          | Solo funciona en US/Canada                 |

### Estrategia de queries (v7)

LinkedIn es lento (~20s/call) y hace soft-ban. Indeed es rápido (~1s/call) y sin riesgo.
Por eso se usan **tres listas de queries independientes**:

| Lista                    | Cantidad | Usado en          | Razón                                      |
|--------------------------|----------|-------------------|--------------------------------------------|
| `QUERIES_LINKEDIN_FULL`  | 12       | Chile             | Queries curadas, sin redundancia            |
| `QUERIES_LINKEDIN_LIGHT` | 6        | Argentina, Colombia| Solo queries genéricas de amplio espectro   |
| `QUERIES_INDEED`         | 27       | Los 3 países      | Todas las queries (Indeed es rápido y gratis)|

**Total calls:** 12 + 6×2 + 27×3 = 105 (vs 162 en v6).

**Anti-ban LinkedIn:** sleep aleatorio `[2, 4, 6, 9]` segundos entre cada call LinkedIn.

**Queries eliminadas de LinkedIn (redundantes):**
`nextjs developer`, `frontend developer typescript`, `django developer`, `fastapi developer`,
`backend python developer`, `fullstack remote latam`, `react remote latam`, `senior fullstack developer`,
`graphql developer`, `ai engineer`, `ingeniero backend`, `desarrollador backend`,
`desarrollador python`, `freelance developer`, `fullstack freelance`.
Estas queries retornaban los mismos jobs que las queries genéricas (57% duplicados en v6).

### Países buscados

- 🇨🇱 Chile — mercado local (LinkedIn FULL: 12 queries)
- 🇦🇷 Argentina — mismo horario UTC-3, gran volumen tech (LinkedIn LIGHT: 6 queries)
- 🇨🇴 Colombia — 2h diferencia, buen mercado tech remoto (LinkedIn LIGHT: 6 queries)

### Pipeline de filtros (en orden)

1. **Dedupe por URL** → elimina duplicados entre búsquedas
2. **Filtro remote** → LinkedIn ya viene filtrado; Indeed se filtra por keywords
3. **Excluir títulos** → elimina tech incompatible (PHP, Angular, .NET, C#, Java, Kotlin, Ruby, Rails, OutSystems, Shiny, Shopify, Odoo, Moodle, Elixir, Golang, React Native) y roles fuera de alcance (Lead, Staff, Principal, Director, Trainee, Práctica). Java usa regex `\bjava\b(?!script)` para no atrapar "javascript".
4. **Excluir empresas** → ver lista EXCLUDE_COMPANIES
5. **Score de match** → puntaje basado en tecnologías encontradas en título y descripción
6. **Filtro de relevancia** → solo pasan trabajos con score ≥ 2 O que sean roles de dev genéricos

### Sistema de scoring

```
Título contiene tech → peso × 2
Descripción contiene tech → peso × 1
2+ techs incompatibles en título → penalización -5
```

Pesos actuales:
- React, Next.js, Node.js, TypeScript → 4
- NestJS, Express → 3
- Python, Django, FastAPI, GraphQL, Flutter → 2

---

## Empresas excluidas (EXCLUDE_COMPANIES)

| Empresa          | Razón                                  |
|------------------|----------------------------------------|
| BairesDev        | Outsourcing masivo, salarios bajos     |
| Core Code io     | Spam de anuncios genéricos, score 0   |
| Klog / Klog.co   | Ex-empleador de Freddy                 |
| Depot Group      | Ex-empleador de Freddy                 |
| Grupo Mil Sabores| Ex-empleador de Freddy                 |
| Grupo Los Robles | Ex-empleador de Freddy                 |
| Dotsolution      | Ex-empleador de Freddy                 |

---

## Metadata en cada CSV

Cada archivo de resultados incluye cabecera de configuración:

```
# CONFIG_VERSION=v7
# TIMESTAMP=20260217_1200
# PAISES=Chile,Argentina,Colombia
# SITES_REMOTE=linkedin
# SITES_HOURS=indeed
# HOURS_OLD=168
# SCORE_MINIMO=2
# QUERIES_LINKEDIN_FULL=12
# QUERIES_LINKEDIN_LIGHT=6
# QUERIES_INDEED=27
# TOTAL_CALLS=105
# TOTAL_RESULTADOS=XX
```

Esto permite a una IA comparar qué configuración produjo mejores resultados.

---

## Fuentes manuales (manual_sources.json)

Portales que JobSpy no soporta pero Freddy revisa manualmente:
- **Computrabajo** (la más repetida en su historial real)
- **GetOnBrd** (buena para Chile/LATAM)
- **Laborum, Trabajando.cl, WeRemoto, VacantesDigitales**
- **Torre, Talent, FindJobit**

> Futuro: GetOnBrd tiene API pública. Podría integrarse para automatizar.

---

## Historial de versiones del script

| Versión | Cambio principal                                              |
|---------|---------------------------------------------------------------|
| v1      | Script inicial, búsquedas básicas                            |
| v2      | Scoring con keywords, filtro is_remote                       |
| v3      | Fix NaN, búsquedas en español, freelance                     |
| v4      | Excluir BairesDev, React Native, tech incompatibles          |
| v5      | LinkedIn/Indeed separados, 3 países, ex-empleadores excluidos|
| v6      | Pesos corregidos: JS peso 4, Python/Flutter peso 2           |
| v7      | LinkedIn queries reducidas (12 CL, 6 AR/CO), sleep anti-ban, Indeed sin cambios. 105 calls vs 162 |
| v7.1    | EXCLUDE_TITLE_KEYWORDS ampliado: PHP, Angular, .NET, C#, Java (regex), Kotlin, Ruby, Rails, OutSystems, Shiny, Shopify, Odoo, Moodle, Lead, Trainee, Practica sin acento. -36 títulos basura |
| v7.2    | Output dual: .csv (datos) + .md (resumen legible con links, agrupado por site). Orden por site → score desc |
| v7.3    | Fix bug "principal engineer" → "principal" (substring no matcheaba "Principal Full Stack Engineer"). Nuevas exclusiones no-dev: qa engineer, quality assurance, automation engineer, designer, ui/ux, data analyst, data engineer, data science, devops, sre, salesforce, apex, support engineer, technical support, observability, migration/upgrade consultant |
| v7.4    | Excluir "senior" absoluto via _is_absolute_senior(). Conserva "semi senior" y "semi-senior". Regex: \bsenior\b con guard semi[\s-]+senior |
| v7.5    | "qa engineer" → "qa" (matchea "QA Manual Analyst" etc). Añadidos: engineering manager, drupal, hana |
| v7.6    | `_is_absolute_senior()` ahora captura `Sr` (abreviatura). Excluir `remote from` en título (trabajo restringido a otro país). Excluir `iot`. |
| v7.7    | Envío de email al terminar el run. `send_email_report()` usa `GMAIL_USER` + `GMAIL_APP_PASSWORD` (env vars). `railway.toml` para deploy en Railway como cron job (lunes y jueves 9am UTC-3). Railway usa Nixpacks para auto-detectar Python + Pipfile, sin Dockerfile. |
| v7.8    | Fix email en Railway: reemplazado SMTP (bloqueado en Hobby plan) por Resend HTTP API. Variables: `RESEND_API_KEY` + `RESEND_TO_EMAIL`. Dependencia `resend` agregada al Pipfile. |

---

## Referencias obligatorias

> ⚠️ Antes de modificar el script, consultar siempre la documentación oficial.
> No inventar parámetros ni comportamientos — verificar contra la fuente real.

- **JobSpy (librería usada)**: https://github.com/speedyapply/JobSpy
  - Parámetros de `scrape_jobs()`, sitios soportados, restricciones por sitio
  - Importante: restricciones de Indeed (`is_remote` + `hours_old` son incompatibles)

---

## Aprendizajes clave

- **El mercado chileno es pequeño** (~9-10 trabajos únicos/día). Sin Argentina y Colombia el volumen es insuficiente.
- **LinkedIn hace soft-ban** si se ejecuta muchas veces seguidas (~2-3 veces en el mismo día). Esperar 12-24h entre ejecuciones.
- **Indeed da mejor calidad** (solo 19% del volumen pero los mejores scores históricos vinieron de ahí).
- **Computrabajo es la fuente #1** del historial real de Freddy pero JobSpy no la soporta.
- **BairesDev y Core Code io** contaminan los resultados con spam. Ya excluidos.
- **React Native ≠ Flutter**. Freddy domina Flutter, no React Native.
- **LinkedIn tiene 57% de duplicados entre queries** (v6). Queries específicas como "django developer" o "nextjs developer" retornan los mismos jobs que "python developer" o "react developer". Se eliminaron las redundantes en v7.
- **Indeed cubre las queries específicas** sin riesgo de ban (~1s/call). No hay razón para reducir queries de Indeed.
- **EXCLUDE_TITLE_KEYWORDS debe usar keywords individuales**, no frases compuestas. `".net developer"` no atrapa `"Desarrollador .Net Senior"`. Usar `".net"` solo.
- **`Sr` no es capturado por `\bsenior\b`**. Se maneja por separado con regex `\bsr\.?\s` en `_is_absolute_senior()`.
- **"Remote from [país]"** indica puesto restringido a ese país específico, no LATAM general. Se excluye con regex `\bremote from\b` en `matches_excluded()`.
- **"java" no se puede excluir con substring** porque `"java" in "javascript"` es True. Se usa regex `\bjava\b(?!script)`.
- **El CSV ordena por site → score DESC**. Primero Indeed, luego LinkedIn, cada grupo por score. El .md es más fácil de leer que el .csv (cada fila del CSV ocupa ~35 líneas por la descripción larga).
- **"principal engineer" no matchea "Principal Full Stack Engineer"** porque la substring incluye "engineer" con palabras en el medio. Usar `"principal"` solo.
- **Roles no-dev contaminan resultados**: QA, Designer, Data Analyst, DevOps, Salesforce, Support Engineer pasan el filtro si no están explícitamente excluidos.
