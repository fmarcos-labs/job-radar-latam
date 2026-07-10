🤖 Proyecto asistido por IA — NO se contabiliza en CV/resume (no es práctica manual real).

# job-radar-latam

Script Python que automatiza la búsqueda de ofertas de trabajo remotas en LATAM
usando [python-jobspy](https://github.com/cullenwatson/JobSpy). Se ejecuta como
cron job en Railway (lunes y jueves 9am CLT) y envía los resultados por email vía Resend.

---

## Requisitos

- Python 3.10+
- `pipenv`

---

## Instalación

```bash
pipenv install
```

---

## Uso local

```bash
pipenv run job1
```

Genera una carpeta `job1/YYYYMMDD_HHMM/` con:
- `results.csv` — datos completos
- `results.md` — resumen legible con links
- `discarded.md` — descartados para revisión manual

---

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `RESEND_API_KEY` | API key de Resend (envío de email) |
| `RESEND_TO_EMAIL` | Email destino del reporte |

---

## Deploy (Railway)

El proyecto se despliega automáticamente desde GitHub.
Railway detecta Python + Pipfile vía Nixpacks, sin Dockerfile.

El cron está configurado en el dashboard de Railway (no en `railway.toml`).