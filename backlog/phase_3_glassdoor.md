# Phase 3: Glassdoor como source opcional

**Estado**: 🟡 Pendiente
**Riesgo**: 🟡 Medio (agregar nuevo sitio, puede aumentar tiempo de scraping)
**Duración estimada**: 5-10 min

## Objetivo
Extender `SITE_NAMES` para incluir "glassdoor" como fuente adicional de empleos.

## Contexto
Glassdoor es una buena fuente para empleos remotos. jobspy soporta este sitio. Solo necesitas agregarlo a la lista.

## Cambio a hacer

En `job1/jobspy_search.py`, línea 19:

**Antes**:
```python
SITE_NAMES = ["indeed", "linkedin", "google", "zip_recruiter"]
```

**Después**:
```python
SITE_NAMES = ["indeed", "linkedin", "google", "zip_recruiter", "glassdoor"]
```

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Busca `SITE_NAMES = [`
- [ ] Agrega `"glassdoor"` al final de la lista
- [ ] Guarda el archivo

## Prueba

```bash
cd job1/
python jobspy_search.py
```

### Checklist post-ejecución

- [ ] Script termina sin errores
- [ ] CSV generado con timestamp
- [ ] CSV tiene datos (> 0 filas)
- [ ] En terminal, en las líneas de búsqueda, ves "glassdoor" entre los sitios procesados
- [ ] Ejemplo esperado:
  ```
  --- Buscando: 'fullstack developer typescript' ---
    Encontrados: XX trabajos (ahora incluye glassdoor)
  ```

## Verificación en CSV

- [ ] Abre el CSV generado
- [ ] Busca la columna `site` y verifica que hay filas con `glassdoor`
- [ ] Revisa que los "glassdoor" jobs tengan `is_remote=True`

## Si falla

1. **Error: Glassdoor scraping failed**
   ```
   Error en 'fullstack developer typescript': glassdoor...
   ```
   → Glassdoor tiene anti-scraping activo. Esto es normal ocasionalmente.
   → Puedes hacer retry o remover "glassdoor" por ahora.

2. **Tiempo de ejecución mucho mayor**
   → Glassdoor es más lento. Esto es esperado. Si > 5 min por query, considerar reducir `results_wanted` o queries.

3. **Menos resultados que Phase 2**
   → Revierte el cambio y continúa (puede ser variación temporal)

## Opcional: Glassdoor deshabilitado

Si Glassdoor falla consistentemente, puedes convertirlo en configurable:

```python
# Línea 11 (después de SEARCH_QUERIES)
INCLUDE_GLASSDOOR = False  # Cambia a True para activar

# Línea 19 (SITE_NAMES)
SITE_NAMES = ["indeed", "linkedin", "google", "zip_recruiter"]
if INCLUDE_GLASSDOOR:
    SITE_NAMES.append("glassdoor")
```

## Siguiente paso

Una vez ✅ Phase 3, puedes pasar a **Phase 4: Queries ampliadas (batch 1)**.

---

### Notas de ejecución

```
Fecha de prueba: ___________
Resultado: ___________
Glassdoor jobs encontrados: ___________
Tiempo de ejecución: ___________
Observaciones: ___________
```
