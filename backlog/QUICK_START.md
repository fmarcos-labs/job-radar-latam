# Quick Start - Job1 Improvements

## 🚀 Cómo usar este backlog

### 1️⃣ Lee primero
```
1. Este archivo (QUICK_START.md)
2. README.md (visión general)
```

### 2️⃣ Ejecuta cada phase en orden

```bash
# Antes de empezar:
cd /home/fmarcosdev/Volumes/Extended/github/CURIOSIDADES

# Para cada phase:
1. Abre backlog/phase_N_xxx.md
2. Lee la documentación
3. Aplica los cambios específicos
4. Corre: cd job1/ && python jobspy_search.py
5. Revisa los resultados
6. Documenta en backlog/TESTING_LOG.md
7. Procede a siguiente phase SI OK
```

### 3️⃣ Si algo falla

```bash
# Revert rápido
cd job1/
git checkout jobspy_search.py

# O edita manualmente los cambios malos
```

---

## 📋 Ordem de Phases

```
Phase 1: Setup & Baseline (sin cambios)
  ↓
Phase 2: Google search_term (+1 parámetro)
  ↓
Phase 3: Glassdoor (+1 site, opcional)
  ↓
Phase 4: Queries Batch 1 (+7 queries, LATAM/NextJs)
  ↓
Phase 5: Queries Batch 2 (+14 queries, Flutter/Python/AI)
  ↓
Phase 6: REMOTE_MODE config (strict/loose/off)
  ↓
Phase 7: MIN_MATCH config (0/1/2)
```

---

## ✅ Checklist General

```
[ ] Phase 1 - ✅ OK
[ ] Phase 2 - ⭕ Pendiente
[ ] Phase 3 - ⭕ Pendiente
[x] Phase 4 - ✅ Completado (aprobado)
[x] Phase 5 - ✅ Completado (aprobado)
[ ] Phase 6 - ⭕ Pendiente
[ ] Phase 7 - ⭕ Pendiente

Después de todas:
[ ] Consolidar cambios en rama
[ ] Crear PR
[ ] Revisar CSV final
[ ] Merge a main
```

---

## 📁 Estructura del Backlog

```
backlog/
├── README.md                  ← Visión general (LEE PRIMERO)
├── QUICK_START.md             ← Este archivo
├── TESTING_LOG.md             ← Diario de pruebas (COMPLETA mientras avanzas)
│
├── phase_1_baseline.md        ← Setup, sin cambios
├── phase_2_google_search_term.md  ← +google_search_term
├── phase_3_glassdoor.md       ← +glassdoor site
├── phase_4_queries_batch1.md  ← +7 queries
├── phase_5_queries_batch2.md  ← +14 queries
├── phase_6_remote_mode.md     ← REMOTE_MODE config
└── phase_7_min_match.md       ← MIN_MATCH config
```

---

## ⏱️ Tiempos Estimados

| Phase | Tiempo | Riesgo |
|-------|--------|--------|
| 1 | 5-10 min | 🟢 Bajo |
| 2 | 5 min | 🟢 Bajo |
| 3 | 5-10 min | 🟡 Medio |
| 4 | 10-15 min | 🟡 Medio |
| 5 | 10-15 min | 🟡 Medio |
| 6 | 15-20 min | 🟠 Medio-Alto |
| 7 | 10 min | 🟠 Medio |
| **TOTAL** | **~1.5-2 horas** | ↕️ Crece |

---

## 🎯 Qué cambios hace cada phase

### Phase 1: Setup & Baseline
- ✅ Sin cambios de código
- ✅ Solo verifica que funciona

### Phase 2: Google search_term
```python
# Agrega una línea:
google_search_term=query,
```

### Phase 3: Glassdoor
```python
# Edita una línea:
SITE_NAMES = [..., "glassdoor"]
```

### Phase 4: Queries Batch 1
```python
# Agrega 7 queries nuevas (LATAM, Next.js)
```

### Phase 5: Queries Batch 2
```python
# Agrega 14 queries nuevas (Flutter, Python, AI)
```

### Phase 6: REMOTE_MODE
```python
# Agrega función is_remote_job() y config
REMOTE_MODE = "strict"  # o "loose" o "off"
```

### Phase 7: MIN_MATCH
```python
# Agrega config
MIN_MATCH = 1  # o 0 o 2
```

---

## 💡 Consejos

1. **No saltes phases**: El orden importa (cada una depende de la anterior)
2. **Documenta todo**: Completa TESTING_LOG.md mientras avanzas
3. **Revert rápido**: Si algo falla, no te asustes. `git checkout job1/jobspy_search.py` revert todo
4. **Test después de cada cambio**: No esperes a hacer todos de una vez
5. **CSV es tu friend**: Abre el CSV generado y revisa datos antes de continuar

---

## 🚨 Si todo se vuelve caos

Opción nuclear (revert completo):

```bash
cd /home/fmarcosdev/Volumes/Extended/github/CURIOSIDADES
git status  # Ver qué cambió
git checkout job1/jobspy_search.py  # Revert todo
# Y vuelve a empezar desde Phase 1
```

---

## 📞 Debugging rápido

### Error: "No se encuentran trabajos"
```
→ Es normal, filtros son estrictos
→ Continúa a siguiente phase
→ O ajusta REMOTE_MODE a "loose" en Phase 6
```

### Error: "ModuleNotFoundError: jobspy"
```
→ Instala: pip install jobspy pandas
```

### Error: "Timeout / Script se cuelga"
```
→ Reduce results_wanted de 40 a 20 en job1/jobspy_search.py línea 73
→ O reduce número de queries
```

### Script lento
```
→ Normal con 27 queries. Espera 8-10 min.
→ O implementa RUN_BATCH config (Phase 5)
```

---

## ✨ Próximos pasos después de todas las phases

1. Consolida cambios en una rama:
   ```bash
   git checkout -b feature/job1-improvements
   ```

2. Revisa todo funciona:
   ```bash
   cd job1/ && python jobspy_search.py
   ```

3. Crea PR con descripción de mejoras

4. Merge a main cuando esté approved

---

## 🔗 Enlaces

- [README.md](./README.md) - Visión general completa
- [TESTING_LOG.md](./TESTING_LOG.md) - Completa esto mientras avanzas
- Cada phase tiene su doc específica (phase_N_xxx.md)

---

**¡Listo! Inicia con Phase 1 → Lee [phase_1_baseline.md](./phase_1_baseline.md)**
