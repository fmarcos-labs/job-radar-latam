# Phase 7: MIN_MATCH configurable

**Estado**: 🟡 Pendiente
**Riesgo**: 🟠 Medio (ajusta umbral de relevancia)
**Duración estimada**: 10 min

## Objetivo
Agregar config `MIN_MATCH` para controlar el umbral mínimo de keywords que debe tener un job.

## Contexto
Actualmente, solo se incluyen jobs con `match_score > 0` (al menos 1 keyword). Esto puede perder jobs sin descripción o descripciones vacías.

Con MIN_MATCH:
- `MIN_MATCH = 1`: Al menos 1 keyword (actual, más restrictivo)
- `MIN_MATCH = 0`: 0 o más keywords (incluye jobs sin descripción)
- `MIN_MATCH = 2`: Al menos 2 keywords (más restrictivo)

## Cambio a hacer

En `job1/jobspy_search.py`, agrega config **ANTES de `def main()`**:

```python
# ===== Configuración de MIN_MATCH =====
MIN_MATCH = 1  # 0 = no filtro, 1 = al menos 1 keyword, 2 = al menos 2 keywords
```

Luego, en `main()`, **reemplaza** línea 121:

**Antes**:
```python
# Quedarse solo con ofertas que al menos matchean 1 keyword
combined = combined[combined["match_score"] > 0]
```

**Después**:
```python
# Filtrar por MIN_MATCH
if MIN_MATCH > 0:
    combined = combined[combined["match_score"] >= MIN_MATCH]
else:
    # MIN_MATCH = 0: incluir todos (even sin keywords)
    pass
```

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Agrega config `MIN_MATCH = 1` (línea ~54, después de REMOTE_MODE)
- [ ] Reemplaza línea 121 con el nuevo código
- [ ] Guarda el archivo

## Test 1: MIN_MATCH = 1 (control, actual)

```bash
cd job1/
# Edita línea 54
MIN_MATCH = 1
python jobspy_search.py
```

**Esperado**: Mismos resultados que Phase 5/6 (match_score >= 1)

Documenta: `results_min_match_1 = XX`

## Test 2: MIN_MATCH = 0

```bash
# Edita línea 54
MIN_MATCH = 0
python jobspy_search.py
```

**Esperado**: Más resultados (incluyendo jobs sin keywords matcheadas)

Documenta: `results_min_match_0 = YY`

**Verificar**: Abre CSV y busca jobs con `match_score=0` → esos son los nuevos.

## Test 3: MIN_MATCH = 2 (opcional, más restrictivo)

```bash
# Edita línea 54
MIN_MATCH = 2
python jobspy_search.py
```

**Esperado**: Menos resultados que 1 (solo jobs muy relevantes)

Documenta: `results_min_match_2 = ZZ`

## Comparación

| MIN_MATCH | Criterio | Resultados esperados | Uso |
|-----------|----------|----------------------|-----|
| 0 | Sin filtro | XX + 30-80% (más) | Para no perder oportunidades |
| 1 | ≥ 1 keyword | XX (actual, balanceado) | Default, buen balance |
| 2 | ≥ 2 keywords | XX - 40% (menos, muy filtrado) | Solo jobs muy relevantes |

## Checklist post-ejecución

- [ ] Test MIN_MATCH=1 OK, resultados = Phase 6
- [ ] Test MIN_MATCH=0 OK, resultados > 1
- [ ] Test MIN_MATCH=2 OK, resultados < 1 (si lo haces)
- [ ] No hay errores en ningún modo
- [ ] CSV tiene todos los datos esperados

## Si algo falla

1. **KeyError: 'match_score'**
   → Verifica que `score_job()` está en el archivo
   → Revisa línea ~57 (se debería calcular antes del filtrado)

2. **MIN_MATCH=0 no agrega resultados**
   → Puede ser que todos los jobs tienen `is_remote` o keywords
   → Intenta con `REMOTE_MODE = "off"` + `MIN_MATCH = 0` para ver diferencia

3. **Sintaxis error**
   → Verifica indentación de if/else

## Recomendación final

Después de Phase 7 (final):
- **Usa `MIN_MATCH = 1` como default** (balanceado)
- **Usa `REMOTE_MODE = "strict"` como default** (seguro)
- Documenta que loose/0-match existen si quieres experimentar

## Archivo final propuesto

Después de todas las phases, tu `jobspy_search.py` debería tener:

```python
# Línea ~50-55
REMOTE_MODE = "strict"  # strict, loose, off
MIN_MATCH = 1           # 0 = sin filtro, 1 = >=1 keyword, 2 = >=2 keywords

# Línea ~52-70
def is_remote_job(row) -> bool:
    # ... función REMOTE_MODE

# Línea ~75-95
def main() -> None:
    # ... scraping ...
    # Aplicar filtros
    combined = combined[combined.apply(is_remote_job, axis=1)]
    # ... otras transformaciones ...
    if MIN_MATCH > 0:
        combined = combined[combined["match_score"] >= MIN_MATCH]
```

## Siguiente paso

✅ **¡Todas las phases completadas!**

Ahora:
1. Crea una rama `feature/job1-improvements`
2. Consolida todos los cambios
3. Crea un PR con descripción de qué agregaste
4. Revisa el CSV final y documenta resultados

---

### Notas de ejecución

```
Fecha de prueba: ___________

Test MIN_MATCH = 1:
  Resultado: ___________
  # Resultados: ___________

Test MIN_MATCH = 0:
  Resultado: ___________
  # Resultados: ___________

Test MIN_MATCH = 2 (opcional):
  Resultado: ___________
  # Resultados: ___________

Observaciones: ___________
Qué MIN_MATCH elegir por default: ___________
```

---

## 🎉 Resumen Final de Todas las Phases

| Phase | Cambio | Riesgo | Estado |
|-------|--------|--------|--------|
| 1 | Baseline (sin cambios) | 🟢 Bajo | ⭕ Pendiente |
| 2 | `google_search_term=query` | 🟢 Bajo | ⭕ Pendiente |
| 3 | Agregar "glassdoor" a SITE_NAMES | 🟡 Medio | ⭕ Pendiente |
| 4 | +7 queries LATAM/NextJs | 🟡 Medio | ⭕ Pendiente |
| 5 | +14 queries Flutter/Python/AI | 🟡 Medio | ⭕ Pendiente |
| 6 | REMOTE_MODE (strict/loose/off) | 🟠 Medio-Alto | ⭕ Pendiente |
| 7 | MIN_MATCH (0/1/2) | 🟠 Medio | ⭕ Pendiente |

**Total**: 7 fases, ~1-2 horas si todo OK.
