# Phase 1: Setup & Baseline

**Estado**: 🟡 Pendiente
**Riesgo**: 🟢 Bajo (sin cambios de código)
**Duración estimada**: 5-10 min

## Objetivo
Validar que el script actual funciona correctamente **sin cambios**. Esto es el baseline contra el cual comparamos todas las mejoras futuras.

## Checklist

- [ ] Asegúrate de tener `jobspy` instalado:
  ```bash
  pip list | grep jobspy
  # Si no aparece:
  pip install jobspy pandas
  ```

- [ ] Ejecuta el script actual sin cambios:
  ```bash
  cd job1/
  python jobspy_search.py
  ```

- [ ] Verifica los resultados:
  - [ ] El script termina sin errores
  - [ ] Se genera un CSV con timestamp (ej: `jobs_results_20260212_2210.csv`)
  - [ ] El CSV tiene > 0 filas (datos encontrados)
  - [ ] En la terminal ves líneas como:
    ```
    --- Buscando: 'fullstack developer typescript' ---
      Encontrados: XX trabajos
    TOTAL trabajos únicos encontrados (relevantes): YY
    ```

## Qué mirar en el CSV

- **Columnas esperadas**: `title`, `company`, `location`, `date_posted`, `job_type`, `min_amount`, `max_amount`, `job_url`, `site`, `search_query`, `match_score`
- **Match score**: debe ser > 0 (al menos 1 keyword del perfil)
- **Site**: debe tener "indeed", "linkedin", "google", "zip_recruiter"
- **is_remote**: todos deben ser `True` (filtro activo en línea 95)

## Si falla

1. **Error de importación**:
   ```
   ModuleNotFoundError: No module named 'jobspy'
   ```
   → Instala: `pip install jobspy pandas`

2. **Error de request/conexión**:
   ```
   URLError, ConnectionError
   ```
   → Probablemente issue de internet. Reintentar en 5 min.

3. **CSV vacío**:
   ```
   TOTAL trabajos únicos encontrados (relevantes): 0
   ```
   → Esto puede pasar. Documenta y continúa (los filtros son estrictos).

## Esperado

✅ Script sin errores
✅ CSV generado con datos relevantes (match_score > 0)
✅ Terminal limpia sin warnings críticos

## Siguiente paso

Una vez ✅ Phase 1, puedes pasar a **Phase 2: Google search_term**.

---

### Notas de ejecución

```
Fecha de prueba: ___________
Resultado: ___________
Observaciones: ___________
```
