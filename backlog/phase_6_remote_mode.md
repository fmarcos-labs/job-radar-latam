# Phase 6: REMOTE_MODE configurable

**Estado**: 🟡 Pendiente
**Riesgo**: 🟠 Medio-Alto (cambia lógica de filtrado, puede eliminar jobs válidos)
**Duración estimada**: 15-20 min

## Objetivo
Agregar config `REMOTE_MODE` (strict/loose/off) para controlar cómo se filtran jobs remotos.

## Contexto
Actualmente solo se filtran jobs con `is_remote==True` (strict). Esto es seguro pero puede perder oportunidades.

Con REMOTE_MODE:
- **strict**: solo `is_remote=True` (actual)
- **loose**: `is_remote=True` O location contiene "remote/remoto/100%" (heurística)
- **off**: sin filtro remoto, todos los jobs

## Cambio a hacer

En `job1/jobspy_search.py`, agrega esto **ANTES de `def main()`**:

```python
# ===== Configuración de REMOTE_MODE =====
REMOTE_MODE = "strict"  # "strict", "loose", o "off"

def is_remote_job(row) -> bool:
    """Determina si un job es remoto basado en REMOTE_MODE."""
    if REMOTE_MODE == "off":
        return True

    # Strict: solo confía en la flag de JobSpy
    if REMOTE_MODE == "strict":
        return row.get("is_remote") == True

    # Loose: is_remote O heurística en location
    if REMOTE_MODE == "loose":
        if row.get("is_remote") == True:
            return True
        location = (row.get("location") or "").lower()
        loose_keywords = ["remote", "remoto", "100%", "latam", "latin america"]
        return any(kw in location for kw in loose_keywords)

    return True
```

Luego, en `main()`, **reemplaza** líneas 93-95:

**Antes**:
```python
# Quedarse solo con trabajos remotos (según flag detectado por JobSpy)
if "is_remote" in combined.columns:
    combined = combined[combined["is_remote"] == True]
```

**Después**:
```python
# Filtrar por modo remoto
if "is_remote" in combined.columns or "location" in combined.columns:
    combined = combined[combined.apply(is_remote_job, axis=1)]
```

## Verificación

- [ ] Abre `job1/jobspy_search.py`
- [ ] Agrega la función `is_remote_job()` completa (antes de `def main()`)
- [ ] Agrega config `REMOTE_MODE = "strict"` (línea ~52)
- [ ] Reemplaza líneas 93-95 con el nuevo código
- [ ] Guarda el archivo

## Test 1: strict (control)

```bash
cd job1/
# Edita línea 53
REMOTE_MODE = "strict"
python jobspy_search.py
```

**Esperado**: Mismos resultados que Phase 5 (solo `is_remote=True`)

Documenta: `results_strict = XX`

## Test 2: loose

```bash
# Edita línea 53
REMOTE_MODE = "loose"
python jobspy_search.py
```

**Esperado**: Más resultados que strict (heurística agregará jobs)

Documenta: `results_loose = YY`

**Verificar**: Abre CSV y busca jobs con `location` que contenga "remote" o "100%" pero `is_remote=False` → esos son los agregados.

## Test 3: off

```bash
# Edita línea 53
REMOTE_MODE = "off"
python jobspy_search.py
```

**Esperado**: Muchos más resultados (incluyendo on-site)

Documenta: `results_off = ZZ`

## Comparación

| REMOTE_MODE | Filtro | Resultados esperados | Uso |
|-------------|--------|----------------------|-----|
| strict | `is_remote=True` | XX (menos, más filtrado) | Actual, más seguro |
| loose | `is_remote=True` OR heurística location | XX + 20-50% (más) | Mejor cobertura LATAM |
| off | ninguno | XX + 100-300% (mucho más) | Para análisis exploratorio |

## Checklist post-ejecución

- [ ] Test strict OK, resultados = Phase 5
- [ ] Test loose OK, resultados > strict
- [ ] Test off OK, resultados > loose
- [ ] No hay errores en ningún modo
- [ ] Función `is_remote_job()` es accesible

## Si algo falla

1. **SyntaxError en `is_remote_job()`**
   → Revisa indentación (Python es sensible)
   → Copia exactamente desde la plantilla

2. **Menos resultados en loose**
   → Significa que los keywords de heurística son muy estrictos
   → Agrega más: `loose_keywords += ["wfh", "home", "anywhere"]`

3. **Resultado off muy grande (>500 jobs)**
   → Es esperado. El filtro `match_score > 0` sigue activo.
   → Puedes agregar filtro adicional si quieres más restricción.

## Recomendación final

Después de Phase 6:
- **Usa `REMOTE_MODE = "strict"` como default** (seguro)
- Documenta que loose/off existen si quieres explorar más

## Siguiente paso

Una vez ✅ Phase 6, puedes pasar a **Phase 7: MIN_MATCH configurable** (últimafase).

---

### Notas de ejecución

```
Fecha de prueba: ___________

Test strict:
  Resultado: ___________
  # Resultados: ___________

Test loose:
  Resultado: ___________
  # Resultados: ___________

Test off:
  Resultado: ___________
  # Resultados: ___________

Observaciones: ___________
Qué modo elegir por default: ___________
```
