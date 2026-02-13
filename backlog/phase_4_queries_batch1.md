# Phase 4: Queries ampliadas (Batch 1)

**Estado**: 🟡 Pendiente
**Riesgo**: 🟡 Medio (más búsquedas = más resultados + tiempo de scraping)
**Duración estimada**: 10-15 min

## Objetivo
Agregar queries nuevas enfocadas en LATAM, Next.js/React con distintos niveles, sin eliminar las existentes.

## Contexto
Las queries actuales (6) son básicas. Queremos expandir de forma incremental con términos LATAM-específicos y variantes de nivel (senior, junior).

## Cambio a hacer

En `job1/jobspy_search.py`, línea 9-16, reemplaza `SEARCH_QUERIES` con:

**Antes**:
```python
SEARCH_QUERIES = [
    "fullstack developer typescript",
    "react next.js developer",
    "node.js nestjs backend developer",
    "flutter developer",
    "frontend developer react typescript",
    "web scraping puppeteer developer",
]
```

**Después**:
```python
SEARCH_QUERIES = [
    # Original (mantener)
    "fullstack developer typescript",
    "react next.js developer",
    "node.js nestjs backend developer",
    "flutter developer",
    "frontend developer react typescript",
    "web scraping puppeteer developer",

    # Batch 1: LATAM remoto
    "full stack developer remote latam",
    "fullstack developer 100% remote chile",
    "nextjs developer latam",
    "react developer latam",

    # Batch 1: Next.js/React nivel senior/mid
    "next.js developer senior",
    "react typescript developer mid-level",
    "nextjs backend developer",
]
```

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Busca `SEARCH_QUERIES = [`
- [ ] Reemplaza SOLO las queries manteniendo la estructura
- [ ] Verifica que `SEARCH_QUERIES` ahora tiene 13 queries (6 originales + 7 nuevas)
- [ ] Guarda el archivo

## Prueba

```bash
cd job1/
python jobspy_search.py
```

⚠️ **Este paso durará más** (4 sitios × 13 queries = ~52 requests). Espera 2-5 minutos.

### Checklist post-ejecución

- [ ] Script termina sin errores
- [ ] CSV generado con timestamp
- [ ] CSV tiene muchos datos (esperado: 50+ filas tras filtrado)
- [ ] En terminal ves "--- Buscando:" para cada una de las 13 queries
- [ ] Final sin errores críticos

## Verificación en CSV

- [ ] Abre el CSV generado
- [ ] Busca columna `search_query`: debes ver mezcla de queries originales + nuevas
- [ ] Verifica match_score > 0 en todos los registros
- [ ] Revisa que la mayoría sean `is_remote=True`

## Comparación de volumen

| Métrica | Phase 3 | Phase 4 esperado |
|---------|---------|-----------------|
| # Queries | ~5-6 | ~13 |
| # Resultados brutos | XX | 2-3x XX |
| # Resultados filtrados | YY | 1.5-2x YY |
| Tiempo ejecución | ~1 min | ~3-5 min |

## Si algo falla

1. **Timeout / Script se cuelga**
   → Algunos sitios son lentos. Espera 10 min y cancela si persiste.
   → Opción: reduce queries a 10 (elimina 3 nuevas).

2. **Error en específica query**
   ```
   Error en 'full stack developer remote latam': ...
   ```
   → Revierte esa query y continúa. No todas las búsquedas trabajan igual.

3. **CSV vacío**
   → Los filtros son estrictos (is_remote=True, match_score > 0). Algunos queries pueden no tener match.

4. **Muchos resultados, lentitud**
   → Reduce `results_wanted=40` a `results_wanted=20` en línea 73.

## Siguiente paso

Una vez ✅ Phase 4, puedes pasar a **Phase 5: Queries ampliadas (Batch 2)**.

---

### Notas de ejecución

```
Fecha de prueba: ___________
Resultado: ___________
Queries ejecutadas: ___________
Tiempo de ejecución: ___________
# Resultados filtrados: ___________
Observaciones: ___________
```
