# FASE 1: Mejoras opcionales futuras

**Status**: ⏸️ PENDIENTE
**Prioridad**: Baja (ejecutar solo si los resultados actuales no son suficientes)
**Dependencias**: FASE_0 completada

---

## Contexto

Estas mejoras son opcionales. El script v7.7 ya funciona bien.
Ejecutar solo si se detecta un problema concreto en los resultados reales.

---

## Tareas

### Tarea 1.1: Integrar GetOnBrd API

- Por qué: Es la fuente #2 más relevante para Chile/LATAM después de Computrabajo. Tiene API pública.
- Archivo: `job1/jobspy_search.py`
- Qué hacer:
  1. Investigar documentación de la API de GetOnBrd
  2. Agregar función `scrape_getonbrd()` análoga a las de LinkedIn/Indeed
  3. Integrar los resultados en el pipeline de filtros existente
  4. Actualizar `CONFIG` con los parámetros nuevos
  5. Actualizar `CLAUDE.md` con la nueva fuente
- Referencia: Ver cómo está implementado `scrape_for_country()` en el script actual

### Tarea 1.2: Ajustar queries o pesos de scoring

- Por qué: Si después de varias ejecuciones reales los resultados son de baja calidad
- Archivo: `job1/jobspy_search.py`
- Qué hacer:
  1. Analizar los `results.csv` de varios runs
  2. Identificar falsos positivos (jobs que pasan pero no interesan)
  3. Identificar falsos negativos (jobs descartados que sí interesaban, ver `discarded.md`)
  4. Ajustar `EXCLUDE_TITLE_KEYWORDS`, pesos en `TECH_WEIGHTS`, o listas de queries
  5. Incrementar versión del CONFIG (v7.8, v7.9, etc.)
  6. Actualizar `CLAUDE.md` con el cambio y el aprendizaje

### Tarea 1.3: Agregar más países

- Por qué: Si el volumen de Chile/Argentina/Colombia sigue siendo bajo
- Candidatos: México (gran mercado tech), Uruguay (buen mercado remoto)
- Archivo: `job1/jobspy_search.py`
- Qué hacer:
  1. Agregar entradas en la lista `paises` de `main()`
  2. Usar `QUERIES_LINKEDIN_LIGHT` para países nuevos (anti-ban)
  3. Verificar que `country_indeed` mapea correctamente para JobSpy
  4. Actualizar metadata del CONFIG
  5. Actualizar `CLAUDE.md`

### Tarea 1.4: Soporte Computrabajo

- Por qué: Es la fuente #1 del historial real de Freddy pero JobSpy no la soporta
- Bloqueante: Computrabajo no tiene API pública conocida — requiere scraping custom
- Archivo: `job1/jobspy_search.py` (o nuevo archivo `job1/computrabajo_scraper.py`)
- Qué hacer:
  1. Investigar si Computrabajo tiene API o si hay que hacer scraping con requests/BeautifulSoup
  2. Si es scraping: evaluar si viola ToS y riesgo de ban
  3. Si es viable: implementar función `scrape_computrabajo()` e integrar al pipeline

---

## Criterios de Aceptación

Cada tarea es independiente. Se considera hecha cuando:
- El script corre sin errores localmente (`pipenv run job1`)
- Los resultados mejoran respecto a la versión anterior (comparar CSV)
- `CLAUDE.md` actualizado con la nueva versión y aprendizajes
