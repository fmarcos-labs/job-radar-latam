# Backlog — CURIOSIDADES (JobSpy Scraper)

**Proyecto**: Buscador de empleo automatizado para Freddy Huaylla
**Tech**: Python + JobSpy + Railway + Gmail
**Script activo**: `job1/jobspy_search.py` (v7.7)

---

## Índice de fases

| Fase | Nombre | Status |
|------|--------|--------|
| [FASE 0](FASE_0_DEPLOY.md) | Deploy en Railway | ⏸️ PENDIENTE |
| [FASE 1](FASE_1_MEJORAS.md) | Mejoras opcionales futuras | ⏸️ PENDIENTE |

---

## Estado actual del script (v7.7)

- ✅ Pipeline completo: scraping → filtros → scoring → output
- ✅ Output dual: `results.csv` + `results.md` + `discarded.md`
- ✅ Anti-ban LinkedIn: sleep aleatorio entre calls
- ✅ Envío de email al terminar (`send_email_report()`)
- ✅ Dockerfile listo
- ✅ `railway.toml` con cron configurado
- ⏸️ Deploy en Railway: pendiente de ejecutar

---

## Flujo de trabajo actual

```
1. Editar job1/jobspy_search.py  →  ajustar queries, pesos, filtros
2. pipenv run job1                →  ejecutar localmente
3. Revisar results.md             →  resumen legible con links
4. Iterar configuración           →  volver al paso 1
```

Post-deploy Railway:
```
Cron dispara lunes y jueves 9am (UTC-3)  →  Railway ejecuta el script
→  Gmail recibe results.md por email
→  Freddy revisa bandeja de entrada
```
