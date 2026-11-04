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
1. Editar job1/config.py / helpers.py →  ajustar queries, pesos, filtros, países
2. Test primero (tests/)              →  fixtures de corridas reales, sin red: `python -m pytest tests/ -q`
3. push a master                      →  el runner del Mac Mini hace rsync a /Users/freddymhs/apps/job-radar-latam/
4. Esperar la corrida programada      →  LaunchDaemon com.jobradar.latam, 10:30 y 17:30 (cron.log, job1/<ts>/)
5. Revisar el email / results.md      →  NUEVOS arriba; el asunto trae versión + sha del commit
6. Comparar corridas por sha          →  results.csv lleva CONFIG_VERSION y GIT_SHA en la cabecera
```

> ⚠️ NO ejecutar el script a mano sin autorización del usuario: corre solo 2×/día y LinkedIn hace soft-ban.
> ⚠️ Si se modifica el script, SIEMPRE actualizar este CLAUDE.md (arquitectura, versión, aprendizajes) en el mismo cambio.
> ⚠️ Un cambio de comportamiento sin bump de versión queda invisible: desde v10.0 el sha del commit va en el email y el CSV.
> ⚠️ Los tests corren con un venv propio (`python3 -m venv` + `pip install python-jobspy pandas resend pytest`); `pipenv` no hace falta.

---

## Estructura de archivos

```
job-radar-latam/
├── CLAUDE.md                            ← este archivo (contexto para IA)
├── Pipfile                              ← dependencias (pipenv run job1)
├── Pipfile.lock                         ← lock file (trackeado, Railway lo necesita)
├── README.md                            ← instrucciones de uso
├── railway.toml                         ← legado (Railway ya no se usa; el deploy es el Mac Mini)
├── .github/workflows/deploy.yml         ← push a master → rsync al Mac Mini + escribe GIT_SHA
├── tests/                               ← pytest con fixtures de corridas reales (sin red)
│   └── fixtures/                        ← results.csv/discarded.md reales + un HTML de job de LinkedIn
└── job1/
    ├── jobspy_search.py                 ← entry point: main() orquesta el flujo
    ├── config.py                        ← configuración: queries, pesos, filtros, MAX_DESC_FETCH, SEEN_FILENAME
    ├── getonbrd.py                      ← GetOnBoard por HTML público: todo desde la tarjeta del listado (v10.2)
    ├── redirector.py                    ← clics del correo: 302 a la URL real y clicks.json (v10.3)
    ├── helpers.py                       ← scraping, memoria (SeenStore), descripción LinkedIn, filtros, scoring, export, email
    ├── manual_sources.json              ← URLs manuales de portales no soportados
    ├── seen.json                        ← (solo Mac Mini) memoria entre corridas; el rsync la excluye
    ├── clicks.json                      ← (solo Mac Mini, radar remoto) primera apertura por clave; el rsync lo excluye
    └── YYYYMMDD_HHMM/                  ← carpeta por run
        ├── results.csv                  ← datos completos (cabecera: CONFIG_VERSION, GIT_SHA, …)
        ├── results.md / results.html    ← NUEVOS arriba + tablas por site (md) · el HTML es el cuerpo del email, con el score pesado
        └── discarded.md                 ← descartados para revisión manual
```

En el Mac Mini además existe `GIT_SHA` en la raíz de la app (lo escribe el deploy; el rsync lo excluye).

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
| `QUERIES_LINKEDIN_FULL`  | 27       | Chile                                 | Queries curadas + stack específico           |
| `QUERIES_LINKEDIN_LIGHT` | 6        | Argentina                             | Solo queries genéricas de amplio espectro   |
| `QUERIES_INDEED`         | 28       | Los 4 países × Indeed y Glassdoor     | Una llamada por sitio (un 403 de Glassdoor no mata Indeed) |

**Anti-ban LinkedIn:** sleep aleatorio `[2, 4, 6, 9]` segundos entre cada call LinkedIn.

**Total calls (recontado 03-11 desde `config.py`):** 27 + 6 + 28×4×2 = **257** (`TOTAL_CALLS`), ~17 min por corrida; más hasta 150 requests de descripción (solo avisos nunca evaluados, sleep 2–4 s).

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

### Pipeline de filtros (en orden, v10.0)

1. **Dedupe por URL y por título+empresa** → el mismo aviso con 3 URLs (por región/re-posteo) es una fila (medido: 53 → 31)
2. **Excluir títulos** y **excluir empresas** → ANTES del fetch, para no gastar requests en lo que se descarta igual
3. **Memoria (`SeenStore`, `job1/seen.json`)** → `is_new` = nunca MOSTRADO en un email; lo ya EVALUADO reusa su descripción guardada (solo LinkedIn: Indeed/Glassdoor la traen siempre). Entradas vencen a los 30 días (`first_run`): un aviso republicado meses después vuelve a ser NUEVO y el archivo no crece sin tope. Escritura atómica (tmp + `os.replace`); un archivo corrupto se aparta como `seen.json.corrupt-<ts>` y se arranca vacío. Se construye ANTES de scrapear: si falla, falla a los 0 min
4. **Descripción de LinkedIn para toda fila de LinkedIn SIN texto** (nunca evaluadas primero) → 1 request por job con sleep 2–4 s, tope `MAX_DESC_FETCH` (150); lo que el tope o un error dejó sin texto se reintenta en la corrida siguiente. 5 fallas seguidas (`MAX_CONSECUTIVE_FETCH_FAILURES`) = bloqueo de LinkedIn → se corta el fetch de esa corrida; 999 y redirect a `/authwall` cuentan como falla. Las descripciones se guardan en la memoria apenas bajan
5. **Filtro remote** → LinkedIn: confía en la búsqueda (`is_remote=True` = `f_WT=2`) salvo híbrido/presencial/on-site **en título o ubicación** (nunca en la descripción: "hybrid cloud", "apps híbridas" y "no presencial" aparecen en avisos remotos); Indeed/Glassdoor: keywords (`REMOTE_KEYWORDS`) en título+descripción+ubicación. El dedupe entre gemelos (mismo título+empresa) prefiere al que no dice híbrido
6. **Filtro LATAM** → jobs de países no-chilenos solo pasan si mencionan apertura regional (`LATAM_KEYWORDS`)
7. **Score de match** → tecnologías en título (×2) y descripción (×1)
8. **Filtro de relevancia** → score ≥ 2; el bypass por título de rol dev (`DEV_TITLE_REGEX`) aplica SOLO a filas sin descripción
9. **Email** → `results.md` abre con `## NUEVOS (n)` por score. `send_email_report` devuelve `True` solo si Resend aceptó el envío; **solo entonces** se marcan como mostrados (`mark_shown`). Si el email falla o falta `.env`, la corrida siguiente los vuelve a mostrar como NUEVOS sin re-pedir descripciones

Los detalles de cada exclusión:

- **Excluir títulos (recall-first, v9.0)** → SOLO se excluye lo que "scorea alto pero está mal" y el score no puede filtrar: `React Native` (scorea por "react" pero es mobile), seniority (Lead/Staff/Principal/Director/Trainee/Práctica), role-types no-dev (QA/Designer/Data*/DevOps/SRE/Salesforce/Support). Los **lenguajes backend** que Freddy no hace (.NET/Java/PHP/Go/Ruby/Kotlin/Elixir) YA NO se excluyen: suman 0 al score → un job puro cae por `score_minimo`, y "Node OR .NET" sobrevive por Node. Regex especiales en `_matches_excluded_title`: `\bcto\b` (C-level), `\bintern(ship)?s?\b` (sin atrapar "International").
- **Excluir empresas** → ver lista EXCLUDE_COMPANIES
- **Relevancia** → regex `full[\s-]?stack|front[\s-]?end|back[\s-]?end|developer|engineer|ingenier|desarrollador|programador` (v9.0). Desde v10.0 solo rescata filas SIN descripción: con texto disponible manda el score (antes dejaba entrar Elixir/.NET/Perl con score 0 — 13/53 el 03-11).

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
# CONFIG_VERSION=v10.0
# GIT_SHA=a1b2c3d
# TIMESTAMP=20260217_1200
# PAISES=Chile,Argentina,Uruguay,Peru
# SITES_REMOTE=linkedin
# SITES_HOURS=indeed,glassdoor
# HOURS_OLD=168
# SCORE_MINIMO=2
# QUERIES_LINKEDIN_FULL=27
# QUERIES_LINKEDIN_LIGHT=6
# QUERIES_INDEED=28
# TOTAL_CALLS=257
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
| v10.0   | **Lo nuevo, con texto real, y el score manda.** Medido sobre 349 corridas y el Gmail de Freddy (03-11): 75–87 % de cada email era repetido, 22/53 filas duplicadas, 13/53 con score 0, y **el 100 % de las filas de LinkedIn llegaban sin descripción** (JobSpy solo la baja con `linkedin_fetch_description=True`). Memoria entre corridas (`SeenStore`): NUEVOS arriba del email, descripción guardada. Descripción de LinkedIn solo para lo nunca evaluado (tope 150, sleep). Filtro remoto de LinkedIn por la búsqueda (`f_WT=2`), no por la palabra. Bypass de título solo sin descripción. Dedupe por título+empresa. Versión + sha del commit en asunto y CSV; el deploy escribe `GIT_SHA`. Suite `tests/` con fixtures reales. |
| v10.1   | **El correo pesa el score a la vista.** El cuerpo iba como texto plano: la tabla markdown llegaba con `\|` y 267 filas iguales, carga cognitiva alta (Freddy, 03-11). Ahora `export_results` escribe también `results.html` y `send_email_report` lo manda como `html` (el `text` sigue de fallback): solo los NUEVOS, en orden de score, fila densa de 13 px sin botones; score ≥ `score_fuerte` (20) en negrita grande verde con el título en negrita, ≥ `score_medio` (10) normal, debajo gris; un 0 sin descripción se marca `s/d` (LinkedIn no dio el texto) para no leerse como mal match. **Ninguna fila se oculta** ni se filtra: cambia el peso, no el contenido. Umbrales en `config.py`. Tests en `test_export.py` (todas las filas, orden, tiers, `s/d`, sin `<button>`). |
| v10.2   | **GetOnBoard como fuente.** El portal tech chileno no tiene API pública (api/v2 da 404), pero su listado se lee sin login y **cada tarjeta trae todo**: título, empresa, modalidad explícita, lugar, en qué países admite residir (remotos), sueldo, fecha «Nov 03» (→ ISO; inequívoco mientras nada pase de 365 días, medido 354) y un resumen del aviso que hace de descripción. Por eso **no se baja la página de ningún aviso**: 2 requests por corrida (`/jobs/programacion`, `/jobs/machine-learning-ai`) y cero riesgo de bloqueo. `?countries=CL` no filtra (313 con y sin él): el listado es global y `pais="Chile"` sale de la tarjeta (ciudad chilena, o remoto que admite Chile, la región o el mundo). Entra al mismo pipeline con `site="getonbrd"` (dedupe título+empresa con LinkedIn/Indeed, memoria de vistos, filtros, score, correo); dos ramas en helpers: la modalidad y el país los dice la tarjeta, no una keyword. Sin ventana de fecha: la memoria ya evita repetidos (Freddy, 03-11). Medido el 03-11: 362 avisos, 328 que LinkedIn/Indeed no trajeron ese día. Fixtures reales en `tests/fixtures/getonbrd/`. Ex-empleadores de `resume.json` en `EXCLUDE_COMPANIES`. |
| v10.3   | **Clics del correo.** Cada link del correo pasa por `job1/redirector.py` (biblioteca estándar, LaunchAgent `com.jobradar.redirector` en el Mac Mini, `radar.fmarcos.dev` por el túnel de Cloudflare): `GET /r/<token>?k=<clave>&u=<url>` anota la **primera apertura** por clave título+empresa (la misma de `seen.json`, así el mismo aviso desde LinkedIn, Indeed o GetOnBoard es un solo registro) en `clicks.json` y responde 302 a la URL real. El radar lo lee y agrega la columna `abierto` al CSV. **No cambia qué se muestra**: solo registra. Sin `RADAR_CLICK_BASE` en el `.env`, los links van directos como siempre; `RADAR_CLICKS_FILE` apunta al archivo (el híbrido lee el del remoto). Token solo en el `.env` del Mac; `clicks.json` excluido del rsync. Gmail no abre links solo, así que el registro es real. |
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

- **LinkedIn llega SIN descripción salvo que se pida (causa raíz de v9 y antes, verificada 03-11).** JobSpy 1.1.82 solo baja la descripción de LinkedIn con `linkedin_fetch_description=True` (`jobspy/__init__.py:45`, `model.py:315`, `linkedin/__init__.py:156`: un request por job, para TODOS). El script nunca lo pasó: 38/38 filas de LinkedIn sin texto en 20261103_1030 (Indeed trae ~3.500 chars). Consecuencias medidas: el filtro «remoto» solo veía el título → 608 de 685 descartes por corrida eran LinkedIn ya devueltos por la búsqueda remota; el score de LinkedIn solo veía el título → scores 0 pasando por el bypass. Los commits «recall-first» (c3b974f) e «ignore is_remote» (485643b) pelearon contra el síntoma.
- **`is_remote=True` en la búsqueda de LinkedIn es `f_WT=2` (`linkedin/__init__.py:98`); el campo `is_remote` que vuelve lo deduce JobSpy de palabras en título+descripción+location (`linkedin/util.py:95`).** Con descripción vacía es título-solo, por eso «no era confiable». La señal buena es la búsqueda: Kraken «Fullstack Engineer» tiene 5.658 chars de descripción y no dice «remote» en ninguno.
- **La memoria guarda la descripción, no solo la clave.** Un aviso evaluado y descartado en la corrida 1 que vuelva en la 2 sin su texto entraría por el bypass de título y gastaría otro request. `remember()` corre apenas se bajan las descripciones; `mark_shown()` recién después del email: si el email falla, la corrida siguiente los muestra como NUEVOS sin volver a pedir nada.
- **Cada job llegaba 28 veces por email** (15.950 filas en 6 meses para 572 avisos únicos). Sin «nuevos desde la última corrida» el email no se lee.
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
