# Testing Log - Job1 Improvements

Este archivo es tu **diario de pruebas**. Complétalo mientras avanzas por cada phase.

## Status General

```
Fecha inicio: ___________
Fase actual: ___________
Status: 🟡 En progreso
```

---

## Phase 1: Setup & Baseline

**Documentación**: [phase_1_baseline.md](./phase_1_baseline.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min
Resultado: ✅ sin errores / ❌ con error
Error (si aplica): ___________
CSV generado: jobs_results_YYYYMMDD_HHMM.csv
# Resultados filtrados: ___________
Observaciones: ___________
```

---

## Phase 2: Google search_term

**Documentación**: [phase_2_google_search_term.md](./phase_2_google_search_term.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min
Resultado: ✅ sin errores / ❌ con error
Error (si aplica): ___________
CSV generado: jobs_results_YYYYMMDD_HHMM.csv
# Resultados vs Phase 1: +___ (diferencia)
Observaciones: ___________
```

---

## Phase 3: Glassdoor

**Documentación**: [phase_3_glassdoor.md](./phase_3_glassdoor.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min
Resultado: ✅ sin errores / ❌ con error
Error (si aplica): ___________
CSV generado: jobs_results_YYYYMMDD_HHMM.csv
# Glassdoor jobs encontrados: ___________
# Resultados totales: ___________
Observaciones: ___________
Incluir Glassdoor en próximas fases: ⭕ SÍ / ❌ NO
```

---

## Phase 4: Queries Batch 1

**Documentación**: [phase_4_queries_batch1.md](./phase_4_queries_batch1.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min
Resultado: ✅ sin errores / ❌ con error
Error (si aplica): ___________
CSV generado: jobs_results_YYYYMMDD_HHMM.csv
# Queries ejecutadas: ___________
# Resultados totales: ___________
# Resultados vs Phase 3: +___ (diferencia)
Queries con error: ___________
Observaciones: ___________
```

---

## Phase 5: Queries Batch 2

**Documentación**: [phase_5_queries_batch2.md](./phase_5_queries_batch2.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min
Resultado: ✅ sin errores / ❌ con error
Error (si aplica): ___________
CSV generado: jobs_results_YYYYMMDD_HHMM.csv
# Queries ejecutadas: ___________
# Resultados totales: ___________
# Resultados vs Phase 4: +___ (diferencia)
Queries con error: ___________
Observaciones: ___________
Considerar RUN_BATCH config: ⭕ SÍ / ❌ NO
```

---

## Phase 6: REMOTE_MODE

**Documentación**: [phase_6_remote_mode.md](./phase_6_remote_mode.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min

Test 1 - REMOTE_MODE = "strict":
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Match con Phase 5: ⭕ SÍ / ❌ NO

Test 2 - REMOTE_MODE = "loose":
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Diferencia vs strict: +___ jobs
  Heurística está bien: ⭕ SÍ / ❌ NO

Test 3 - REMOTE_MODE = "off":
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Diferencia vs loose: +___ jobs

REMOTE_MODE elegido por default: ___________
Error (si aplica): ___________
Observaciones: ___________
```

---

## Phase 7: MIN_MATCH

**Documentación**: [phase_7_min_match.md](./phase_7_min_match.md)

```
Estado: ⭕ Pendiente | 🟡 En progreso | ✅ OK | ❌ FAILED
Fecha: ___________
Duración: ___________ min

Test 1 - MIN_MATCH = 1:
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Match con Phase 6: ⭕ SÍ / ❌ NO

Test 2 - MIN_MATCH = 0:
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Diferencia vs 1: +___ jobs

Test 3 - MIN_MATCH = 2 (opcional):
  Resultado: ✅ OK / ❌ FAILED
  # Resultados: ___________
  Diferencia vs 1: -___ jobs

MIN_MATCH elegido por default: ___________
Error (si aplica): ___________
Observaciones: ___________
```

---

## 📊 Resumen Final

```
Fecha inicio: ___________
Fecha fin: ___________
Tiempo total: ___________ horas

Phases completadas: ___ / 7

Configuración final elegida:
  - REMOTE_MODE: ___________
  - MIN_MATCH: ___________
  - SITE_NAMES: ___________
  - # Queries: ___________

CSV final:
  - Ruta: ___________
  - # Resultados: ___________
  - Queries representadas: ___________

Próximos pasos:
  [ ] Crear rama feature/job1-improvements
  [ ] Consolidar cambios en jobspy_search.py
  [ ] Crear PR con descripción
  [ ] Revisar CSV final
  [ ] Merge a main
  [ ] Documenta decisions en README.md de job1/

Notas adicionales:
___________
___________
___________
```

---

## 🔗 Quick Links

- [Phase 1: Setup & Baseline](./phase_1_baseline.md)
- [Phase 2: Google search_term](./phase_2_google_search_term.md)
- [Phase 3: Glassdoor](./phase_3_glassdoor.md)
- [Phase 4: Queries Batch 1](./phase_4_queries_batch1.md)
- [Phase 5: Queries Batch 2](./phase_5_queries_batch2.md)
- [Phase 6: REMOTE_MODE](./phase_6_remote_mode.md)
- [Phase 7: MIN_MATCH](./phase_7_min_match.md)

---

## Revert rápido (si algo sale mal)

```bash
# Si un cambio rompió todo, revert a última versión conocida
cd job1/
git checkout jobspy_search.py  # Revert completo
# O edita manualmente lo que te indica la phase
```
