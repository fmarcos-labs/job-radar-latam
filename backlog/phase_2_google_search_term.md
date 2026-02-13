# Phase 2: Google search_term

**Estado**: 🟡 Pendiente
**Riesgo**: 🟢 Bajo (cambio mínimo, solo parámetro, no afecta otros sitios)
**Duración estimada**: 5 min

## Objetivo
Agregar `google_search_term=query` al parámetro de `scrape_jobs()` para optimizar búsquedas en Google Jobs.

## Contexto
Según docs de jobspy, Google Jobs funciona mejor cuando se pasa `google_search_term` en lugar de `search_term`. Este cambio NO afecta a Indeed, LinkedIn ni Zip Recruiter.

## Cambio a hacer

En `job1/jobspy_search.py`, línea 68-78:

**Antes**:
```python
jobs = scrape_jobs(
    site_name=SITE_NAMES,
    search_term=query,
    location="Chile",
    is_remote=True,
    results_wanted=40,
    hours_old=168,
    country_indeed="Chile",
    description_format="markdown",
    verbose=1,
)
```

**Después**:
```python
jobs = scrape_jobs(
    site_name=SITE_NAMES,
    search_term=query,
    google_search_term=query,  # ← NUEVA LÍNEA
    location="Chile",
    is_remote=True,
    results_wanted=40,
    hours_old=168,
    country_indeed="Chile",
    description_format="markdown",
    verbose=1,
)
```

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Busca la línea `site_name=SITE_NAMES,`
- [ ] Después de `search_term=query,`, agrega una nueva línea con `google_search_term=query,`
- [ ] Guarda el archivo

## Prueba

```bash
cd job1/
python jobspy_search.py
```

### Checklist post-ejecución

- [ ] Script termina sin errores
- [ ] CSV generado con timestamp
- [ ] CSV tiene > 0 filas
- [ ] En terminal ves "Encontrados: XX trabajos" sin aumentos sospechosos

## Comparación

Si Phase 1 encontró 20 trabajos en total:
- **Phase 2 esperado**: 20-25 trabajos (Google puede agregar algunos)
- **Phase 2 preocupante**: 0 trabajos o error de request

## Si falla

1. **TypeError: scrape_jobs() got an unexpected keyword argument 'google_search_term'**
   → Revisa que jobspy esté actualizado: `pip install --upgrade jobspy`

2. **Menos resultados que Phase 1**
   → Revierte el cambio y continúa (puede ser variación temporal)

## Siguiente paso

Una vez ✅ Phase 2, puedes pasar a **Phase 3: Glassdoor**.

---

### Notas de ejecución

```
Fecha de prueba: ___________
Resultado: ___________
Diferencia de resultados vs Phase 1: ___________
Observaciones: ___________
```
