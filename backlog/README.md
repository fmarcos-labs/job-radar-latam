# Job1 - Plan de Mejoras Incrementales

## Objetivo
Mejorar el scraper `job1/jobspy_search.py` de forma **segura y gradual**, validando cada cambio antes de pasar al siguiente. Esto evita el problema anterior donde muchos cambios juntos causaron fallos.

## Filosofía
✅ **Una fase = un cambio pequeño**
✅ **Testear cada fase antes de pasar a la siguiente**
✅ **Revertir fácilmente si algo falla**
✅ **Documentar qué funcionó y qué no**

---

## Fases de Prueba

### 📋 Phase 1: Setup & Baseline
**Estado**: 🟡 Pendiente
**Riesgo**: 🟢 Bajo (sin cambios de código)

Validar que el script actual funciona correctamente sin cambios.

📄 [Ver Phase 1](./phase_1_baseline.md)

---

### 📋 Phase 2: Google search_term
**Estado**: 🟡 Pendiente
**Riesgo**: 🟢 Bajo (cambio mínimo, no afecta otros sitios)

Agregar `google_search_term=query` al parámetro de `scrape_jobs()`.

📄 [Ver Phase 2](./phase_2_google_search_term.md)

---

### 📋 Phase 3: Glassdoor como source opcional
**Estado**: 🟡 Pendiente
**Riesgo**: 🟡 Medio (agregar nuevo sitio)

Extender `SITE_NAMES` para incluir "glassdoor" de forma opcional.

📄 [Ver Phase 3](./phase_3_glassdoor.md)

---

### 📋 Phase 4: Queries ampliadas (batch 1)
**Estado**: ✅ Completado (aprobado por usuario)
**Riesgo**: 🟡 Medio (más búsquedas = más resultados)

Agregar queries nuevas sin eliminar las existentes (LATAM remoto, Next.js/React senior/junior).

📄 [Ver Phase 4](./phase_4_queries_batch1.md)

---

### 📋 Phase 5: Queries ampliadas (batch 2)
**Estado**: ✅ Completado (aprobado por usuario)
**Riesgo**: 🟡 Medio (más búsquedas)

Agregar queries para Flutter BLoC/Clean Architecture, Python junior, AI/automation.

📄 [Ver Phase 5](./phase_5_queries_batch2.md)

---

### 📋 Phase 6: REMOTE_MODE configurable
**Estado**: 🟡 Pendiente
**Riesgo**: 🟠 Medio-Alto (cambia lógica de filtrado)

Agregar config `REMOTE_MODE` (strict/loose/off) con heurística por location.

📄 [Ver Phase 6](./phase_6_remote_mode.md)

---

### 📋 Phase 7: MIN_MATCH configurable
**Estado**: 🟡 Pendiente
**Riesgo**: 🟠 Medio (ajusta umbral de keywords)

Agregar config `MIN_MATCH` para permitir descripciones vacías o resultados sin keywords.

📄 [Ver Phase 7](./phase_7_min_match.md)

---

## ✅ Checklist para cada fase

Cuando hagas una fase:

1. **Leer la documentación de la fase** (ej: `phase_2_google_search_term.md`)
2. **Aplicar SOLO los cambios descritos** (no hagas más)
3. **Ejecutar el script** y verificar que funciona:
   ```bash
   cd job1/
   python jobspy_search.py
   ```
4. **Revisar el CSV generado** (verifica que tenga datos, no esté vacío)
5. **Revisar el print en terminal** (sin errores)
6. **Si todo OK**: marca la fase como ✅ DONE en el README
7. **Si algo falla**:
   - Revert el cambio (`git checkout job1/jobspy_search.py`)
   - Documenta el error en la sección de notas de la fase
   - Pregunta qué ajustar

---

## 📝 Notas de pruebas

Mientras avanzas, documenta aquí:

- **Phase 1**:
- **Phase 2**:
- **Phase 3**:
- **Phase 4**: ✅ Completado (aprobado). Resultados recientes: 7 filas tras filtros estrictos.
- **Phase 5**: ✅ Completado (aprobado). Resultados recientes: 7 filas tras filtros estrictos.
- **Phase 6**:
- **Phase 7**:

---

## 🚀 Comando rápido de prueba

Desde la raíz del proyecto:
```bash
cd job1/ && python jobspy_search.py && echo "✅ OK" || echo "❌ FAILED"
```

---

## 📊 Próximos pasos después de todas las fases

Una vez todas las fases estén ✅:
- Consolida todo en una rama de feature
- Crea un PR con los cambios incrementales validados
- Revisa el CSV final con todos los cambios activos

---

## 🔗 Referencias

- **jobspy docs**: https://github.com/Bunsly/JobSpy
- **Current baseline**: `job1/jobspy_search.py` (sin cambios)
- **Manual sources**: `job1/manual_sources.json` (referencia, no usado por scraper)
