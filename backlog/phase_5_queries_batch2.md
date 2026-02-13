# Phase 5: Queries ampliadas (Batch 2)

**Estado**: 🟡 Pendiente
**Riesgo**: 🟡 Medio (más queries aún + tiempo de scraping)
**Duración estimada**: 10-15 min

## Objetivo
Agregar queries específicas para Flutter (BLoC/Clean Architecture), Python junior, y AI/automation.

## Contexto
Estas queries amplían el targeting hacia stacks complementarios (Flutter, Python) y herramientas de automation (Puppeteer, Strapi, etc.).

## Cambio a hacer

En `job1/jobspy_search.py`, línea 9-23 (después de Phase 4), agrega estas queries al final:

**Agregar a SEARCH_QUERIES**:
```python
SEARCH_QUERIES = [
    # Mantener todas las anteriores (6 + 7 = 13 queries)

    # Batch 2: Flutter con Clean Architecture
    "flutter clean architecture developer",
    "flutter bloc pattern",
    "flutter bloc developer",
    "flutter remote latam",

    # Batch 2: Python junior
    "python developer junior",
    "python backend junior",
    "python junior latam",

    # Batch 2: AI & Automation
    "automation engineer puppeteer",
    "whatsapp business api developer",
    "openai developer",
    "ai engineer javascript",
    "typescript ai automation",
    "strapi graphql developer",
    "supabase developer",
]
```

**Resultado**: 13 (anteriores) + 14 (nuevas) = **27 queries totales**

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Busca el final de `SEARCH_QUERIES` (después de Phase 4)
- [ ] Agrega exactamente las 14 queries nuevas al final
- [ ] Verifica que `SEARCH_QUERIES` ahora tiene ~27 queries
- [ ] Guarda el archivo

## Prueba

```bash
cd job1/
python jobspy_search.py
```

⚠️ **Este paso durará más** (4-5 sitios × 27 queries = ~100+ requests). Espera 5-10 minutos.

### Checklist post-ejecución

- [ ] Script termina sin errores (puede tomar bastante tiempo)
- [ ] CSV generado con timestamp
- [ ] CSV tiene muchos datos (esperado: 100+ filas tras filtrado)
- [ ] En terminal ves todas las 27 queries procesadas
- [ ] Final sin errores críticos

## Verificación en CSV

- [ ] Abre el CSV generado
- [ ] Busca columna `search_query`: debes ver mezcla de todas las queries
- [ ] Revisa algunos ejemplos:
  - Jobs con `search_query="flutter bloc developer"` → deben matchear keywords Flutter
  - Jobs con `search_query="python junior latam"` → deben tener Python en description
  - Jobs con `search_query="openai developer"` → deben tener OpenAI/AI keywords

## Comparación de volumen

| Métrica | Phase 4 | Phase 5 esperado |
|---------|---------|-----------------|
| # Queries | ~13 | ~27 |
| # Resultados brutos | 2-3x Phase 3 | 2x Phase 4 |
| # Resultados filtrados | YY | 1.5-2.5x YY |
| Tiempo ejecución | ~3-5 min | ~8-10 min |

## Si algo falla

1. **Timeout / Script se cuelga en query específica**
   ```
   --- Buscando: 'flutter bloc pattern' ---
   (se cuelga aquí)
   ```
   → Esta query puede ser problemática. Comenta esa línea y retenta.
   → Aumenta timeout del script si es necesario.

2. **Error memoria o recursos**
   ```
   MemoryError, ResourceWarning
   ```
   → Reduce `results_wanted=40` a `results_wanted=15` en línea 73.
   → O divide queries en submandos (corre solo flutter queries, luego python, etc.).

3. **CSV vacío o muy pocos resultados**
   → El filtro `is_remote=True` es estricto para algunos queries.
   → Revisa Phase 6 para ajustar REMOTE_MODE.

4. **Demasiado lento**
   → Limita a 20 queries máximo (elimina 7 menos relevantes).
   → O corre por lotes separados.

## Optimización opcional

Si Phase 5 es muy lento, puedes crear **variantes**:

```python
# En línea 11, ANTES de SEARCH_QUERIES
RUN_BATCH = "all"  # "all", "core", "extended", "flutter", "python", "ai"

# Luego, condicional:
SEARCH_QUERIES = [
    # Core (siempre)
    "fullstack developer typescript",
    "react next.js developer",
    "node.js nestjs backend developer",
]

if RUN_BATCH in ["all", "extended"]:
    SEARCH_QUERIES += [
        # Batch 1
        "full stack developer remote latam",
        ...
    ]

if RUN_BATCH in ["all", "flutter"]:
    SEARCH_QUERIES += [
        # Flutter queries
        ...
    ]
```

Luego cambias `RUN_BATCH = "core"` para test rápido o `RUN_BATCH = "all"` para full.

## Siguiente paso

Una vez ✅ Phase 5, puedes pasar a **Phase 6: REMOTE_MODE configurable** (opcional, más avanzado).

---

### Notas de ejecución

```
Fecha de prueba: ___________
Resultado: ___________
Queries ejecutadas: ___________
Tiempo de ejecución: ___________
# Resultados filtrados: ___________
Observaciones (queries lentas o con error): ___________
```
