🤖 Proyecto asistido por IA — NO se contabiliza en CV/resume (no es práctica manual real).

# job-radar-latam

Script Python que automatiza la búsqueda de ofertas de trabajo remotas en LATAM
usando [python-jobspy](https://github.com/speedyapply/JobSpy). Corre en el Mac Mini como
LaunchDaemon (`com.jobradar.latam`, 10:30 y 17:30) y envía los resultados por email vía Resend:
los avisos NUEVOS arriba, y el asunto con la versión y el sha del commit que los produjo.

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
| `RADAR_CLICK_BASE` | Opcional. Base del redirector (`https://radar.fmarcos.dev/r/<token>`): si está, cada link del correo pasa por `job1/redirector.py` y se registra la primera apertura; sin ella los links van directos |
| `RADAR_CLICK_TOKEN` | Opcional. Lo exige el redirector (`job1/redirector.py`) para aceptar clics; sin token el servicio no arranca |
| `RADAR_CLICKS_FILE` | Opcional. Ruta del `clicks.json` que escribe el redirector y lee el radar para la columna `abierto` (default `job1/clicks.json`) |

---

## Tests (sin red, con corridas reales)

```bash
python3 -m venv ~/.local/share/virtualenvs/job-radar-latam-local
~/.local/share/virtualenvs/job-radar-latam-local/bin/pip install python-jobspy pandas resend pytest
~/.local/share/virtualenvs/job-radar-latam-local/bin/python -m pytest tests/ -q
```

Los fixtures en `tests/fixtures/` son un `results.csv`/`discarded.md` reales y un HTML de un job de
LinkedIn; el HTTP se inyecta, nunca se toca LinkedIn desde los tests.

---

## Deploy (Mac Mini)

`push` a `master` → `.github/workflows/deploy.yml` (runner self-hosted en el Mac Mini) hace
`rsync` a `/Users/freddymhs/apps/job-radar-latam/`, excluyendo `.env`, `run.sh`, `cron.log`,
las corridas `job1/20*`, la memoria `job1/seen.json`, los clics `job1/clicks.json` y `GIT_SHA`; después escribe `GIT_SHA`
con el commit desplegado (es lo que va al asunto del email y al CSV).

El scheduler es el LaunchDaemon `/Library/LaunchDaemons/com.jobradar.latam.plist` (10:30 y 17:30,
log en `cron.log`). No se corre a mano: LinkedIn hace soft-ban.

`railway.toml` es legado de cuando corría en Railway; no se usa.