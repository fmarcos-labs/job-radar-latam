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
| Glassdoor   | `hours_old=168`      | Mismos parámetros que Indeed. Llamado junto a Indeed en el mismo `scrape_jobs()`. |
| Google      | ❌ eliminado          | Retorna 0 resultados para LATAM            |
| ZipRecruiter| ❌ eliminado          | Solo funciona en US/Canada                 |

### Estrategia de queries (v7)

LinkedIn es lento (~20s/call) y hace soft-ban. Indeed es rápido (~1s/call) y sin riesgo.
Por eso se usan **tres listas de queries independientes**:

| Lista                    | Cantidad | Usado en                              | Razón                                      |
|--------------------------|----------|---------------------------------------|--------------------------------------------|
| `QUERIES_LINKEDIN_FULL`  | 12       | Chile                                 | Queries curadas, sin redundancia            |
| `QUERIES_LINKEDIN_LIGHT` | 6        | Argentina                             | Solo queries genéricas de amplio espectro   |
| `QUERIES_INDEED`         | 27       | Los 4 países (Indeed + Glassdoor)     | Todas las queries. Each call scrapes both. |

**Anti-ban LinkedIn:** sleep aleatorio `[2, 4, 6, 9]` segundos entre cada call LinkedIn.

**Total calls:** 12 + 6 + 27×4 = 126 (vs 105 en v7.7).

**Anti-ban LinkedIn:** sleep aleatorio `[2, 4, 6, 9]` segundos entre cada call LinkedIn.

**Queries eliminadas de LinkedIn (redundantes):**
`nextjs developer`, `frontend developer typescript`, `django developer`, `fastapi developer`,
`backend python developer`, `fullstack remote latam`, `react remote latam`, `senior fullstack developer`,
`graphql developer`, `ai engineer`, `ingeniero backend`, `desarrollador backend`,
`desarrollador python`, `freelance developer`, `fullstack freelance`.
Estas queries retornaban los mismos jobs que las queries genéricas (57% duplicados en v6).

### Países buscados

- 🇨🇱 Chile — mercado local, UTC-3/-4 (LinkedIn FULL: 12 queries)
- 🇦🇷 Argentina — UTC-3 fijo, 0-1h diff, mayor volumen tech LATAM hispano (LinkedIn LIGHT: 6 queries)
- 🇺🇾 Uruguay — UTC-3 fijo, 0-1h diff, bajo volumen pero remoto-friendly (solo Indeed+Glassdoor)
- 🇵🇪 Peru — UTC-5 fijo, 1-2h diff, mercado creciente (solo Indeed+Glassdoor)

### Pipeline de filtros (en orden)

1. **Dedupe por URL** → elimina duplicados entre búsquedas
2. **Filtro remote** → LinkedIn ya viene filtrado; Indeed/Glassdoor se filtra por keywords
3. **Excluir títulos (recall-first, v9.0)** → SOLO se excluye lo que "scorea alto pero está mal" y el score no puede filtrar: `React Native` (scorea por "react" pero es mobile), seniority (Lead/Staff/Principal/Director/Trainee/Práctica), role-types no-dev (QA/Designer/Data*/DevOps/SRE/Salesforce/Support). Los **lenguajes backend** que Freddy no hace (.NET/Java/PHP/Go/Ruby/Kotlin/Elixir) YA NO se excluyen: suman 0 al score → un job puro cae por `score_minimo`, y "Node OR .NET" sobrevive por Node. Regex especiales en `_matches_excluded_title`: `\bcto\b` (C-level), `\bintern(ship)?s?\b` (sin atrapar "International").
4. **Excluir empresas** → ver lista EXCLUDE_COMPANIES
5. **Filtro LATAM** → jobs de países no-chilenos solo pasan si mencionan apertura regional (LATAM_KEYWORDS)
6. **Score de match** → puntaje basado en tecnologías encontradas en título y descripción
7. **Filtro de relevancia** → solo pasan trabajos con score ≥ 2 O título de rol dev genérico. Regex ampliado (v9.0): `full[\s-]?stack|front[\s-]?end|back[\s-]?end|developer|engineer|ingenier|desarrollador|programador` — antes no cubría "Full Stack"/"Back End" (con espacio), "engineer" ni "programador", matando "Software Engineer" con descripción vacía.

### Sistema de scoring

```
Título contiene tech → peso × 2
Descripción contiene tech → peso × 1
2+ techs incompatibles en título → penalización -5
```

Pesos actuales (v9.0):
- **CORE_TECH**: JavaScript, TypeScript, React, Next.js, `node` (bare, cubre node.js/nodejs) → 4 · NestJS, Express, FastAPI → 3 · Python, Django, GraphQL, Flutter → 2
- **AI_TECH** (peso 3, solo tokens multi-palabra seguros — NADA de "ai"/"ia"/"rag" sueltos): openai, langchain, llm, genai, "generative ai", chatbot, "ai engineer/developer/agent", "agentes ia", "fullstack ia", "inteligencia artificial"… · machine learning / prompt engineering / vector database → 2
- **PLATFORM_TECH**: aws → 3 · serverless, microservicios → 2 (alta demanda + real en Depot/GeoTrans)
- **SECONDARY_TECH** (peso 1): mysql, mongodb, mongoose, postgres, prisma, supabase, api, rest, etc.

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
# CONFIG_VERSION=v7.9
# TIMESTAMP=20260217_1200
# PAISES=Chile,Argentina,Uruguay,Peru
# SITES_REMOTE=linkedin
# SITES_HOURS=indeed,glassdoor
# HOURS_OLD=168
# SCORE_MINIMO=2
# QUERIES_LINKEDIN_FULL=12
# QUERIES_LINKEDIN_LIGHT=6
# QUERIES_INDEED=27
# TOTAL_CALLS=126
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
| v7.9    | Colombia reemplazada por Uruguay (UTC-3). Agregado Peru (UTC-5). Solo Chile usa FULL (12q), resto LIGHT (6q). Glassdoor descartado: no soporta LATAM excepto Brazil/Mexico. 138 calls totales (vs 105 en v7). URL repo JobSpy actualizada a speedyapply/JobSpy. |
| v8.0    | Glassdoor integrado junto a Indeed (mismo `scrape_jobs()` call). LinkedIn reducido: solo Chile FULL + Argentina LIGHT (Uruguay/Peru solo Indeed+Glassdoor). Nuevo filtro LATAM en pipeline: jobs no-chilenos solo pasan si descripción menciona apertura regional. 126 calls totales. |
| v8.1    | Email subject cambiado a `⭐ Job Radar LATAM — {total} trabajos — {run_id}`. Agregados headers `X-Priority: 1` e `Importance: high` para mayor visibilidad en inbox. |
| v9.0    | **Recall-first + calibración con 117 corridas reales.** Filosofía: mostrar más, el score rankea (EXCLUDE mínimo). Lenguajes backend fuera del EXCLUDE (self-filtran por score 0). +`AI_TECH` (16 kw IA/LLM, peso 3) +`PLATFORM_TECH` (aws 3, serverless/microservicios 2). +javascript, +`node` bare, fastapi 2→3, +mysql/mongodb. **4 bugs de substring fixeados (víctimas reales):** `cto`⊂contractor/proyecto (61), `angular` mató 93 fullstack-Node, `intern`⊂international, `go developer`⊂django. Relevance regex ampliado (engineer/full stack c-espacio/programador). +`americas` en LATAM_KEYWORDS. |

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
- **"java" ya NO se excluye (v9.0, recall)**: suma 0 al score → un "Java Developer" puro cae por `score_minimo`, y "Node OR Java" sobrevive por Node. (Antes: regex `\bjava\b(?!script)` para no atrapar "javascript" — el substring `"java" in "javascript"` es True.)
- **Indeed y Glassdoor deben llamarse por separado**: Si se combinan en `site_name=["indeed", "glassdoor"]` y Glassdoor lanza un error 403, el `except` captura el fallo de todo el call y Indeed queda en 0 resultados. Solución: iterar sobre `SITES_HOURS` haciendo un `scrape_jobs()` por sitio. Verificado en run 20260305: Indeed devolvió 0 porque Glassdoor fallaba en la llamada combinada.
- **"home office" es el término LATAM para remoto**: En Chile/LATAM las ofertas usan "home office" en vez de "remoto". Si no está en `remote_keywords`, cientos de jobs legítimos caen en el filtro remote. Verificado en run 20260305: 432 jobs de Chile descartados incorrectamente por esta causa.
- **`is_remote` en pandas no siempre es Python `True`**: JobSpy puede retornar `1`, `"True"` u otros valores. Usar `in (True, 1, "True", "true")` en vez de `is True`.
- **Glassdoor y el asterisco (*)**: El * en la lista de países de JobSpy indica "oficialmente verificado", NO "el único que funciona". Issue #277 confirma que Malaysia (sin *) devuelve resultados. El asterisco era un falso bloqueante. Glassdoor funciona globalmente; el error de 0 resultados fue por user-agent desactualizado, no por el país.
- **El CSV ordena por site → score DESC**. Primero Indeed, luego LinkedIn, cada grupo por score. El .md es más fácil de leer que el .csv (cada fila del CSV ocupa ~35 líneas por la descripción larga).
- **"principal engineer" no matchea "Principal Full Stack Engineer"** porque la substring incluye "engineer" con palabras en el medio. Usar `"principal"` solo.
- **Roles no-dev contaminan resultados**: QA, Designer, Data Analyst, DevOps, Salesforce, Support Engineer pasan el filtro si no están explícitamente excluidos.
- **Filosofía RECALL > precisión (v9.0)**: para alguien buscando empleo, el costo de un falso-kill (perder buen empleo) >>> el de un falso-pass (ver uno malo, saltearlo en 1 seg). El EXCLUDE debe ser MÍNIMo — solo lo que "scorea alto pero está mal" (react native, seniority, role-types no-dev). Todo lo demás pasa y el score lo rankea; `score_minimo=2` es el filtro suave.
- **Substring mata en silencio — validar SIEMPRE contra `discarded.md` real antes de agregar un token de exclusión.** Bugs históricos confirmados con víctimas reales: `cto`⊂"contra**cto**r"/"proye**cto**" (61 jobs de perfil), `angular` mató 93 fullstack-Node (muchos "Node OR Angular"), `intern`⊂"**Intern**ational", `go developer`⊂"djan**go developer**". Regla: token corto de exclusión → regex `\bword\b`, NUNCA substring. Auditar el EXCLUDE contra el historial de corridas cada calibración.
- **bare `node`**: los títulos reales dicen "Node Developer"/"Node js"/"Node OR .NET" sin `.js`. Usar key `"node"` (cubre node.js y nodejs por substring, sin doble-conteo). NO hacer lo mismo con `"next"` (⊂ "context", inseguro).
- **`node.js`/`nodejs` como keys separadas causaban falso-cero**: "Fullstack Node Developer" scoreaba 0 → se filtraba pese a ser el stack #1. Verificado: 625 ocurrencias de "Node" a secas en las 117 corridas.
