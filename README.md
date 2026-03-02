# CURIOSIDADES — Buscador de Empleo (job1)

Script Python que busca ofertas de trabajo remotas en LATAM usando **python-jobspy**.

---

## Requisitos

- Python 3.10+
- `pipenv` (instalar una vez: `pip install pipenv`)

---

## Instalación

```bash
cd ~/Volumes/Extended/github/CURIOSIDADES
pipenv install
```

---

## Uso

```bash
pipenv run job1
```

Genera un CSV con los resultados en `job1/jobs_results_YYYYMMDD_HHMM.csv`.

> ⚠️ Esperar al menos 12-24h entre ejecuciones para evitar soft-ban de LinkedIn.
