# CURIOSIDADES – Jobs (`job1` y `job2`)

Este proyecto tiene **dos scripts de búsqueda de trabajo**:

- `job1`: usa **python-jobspy** para buscar en varios job boards.
- `job2`: usa **JobFunnel** para otra búsqueda alternativa.

La forma recomendada de usarlos es con **Pipenv**, parecido a usar `npm run` en Node.

---

## 1. Requisitos

- Python **3.10** instalado.
- `pip` funcionando en tu terminal (`pip` o `pip3`).

Opcional pero recomendado:

- `pipenv` para manejar el entorno virtual (como `npm` + `nvm`).

Instalar `pipenv` (solo una vez en tu máquina):

```bash
pip install pipenv
# o
pip3 install pipenv
```

---

## 2. Instalación del proyecto (con Pipenv)

Siempre trabaja desde la carpeta raíz del proyecto, donde está este `README.md` y el `Pipfile`:

```bash
cd ~/Volumes/Extended/github/CURIOSIDADES
```

Instalar dependencias del `Pipfile`:

```bash
pipenv install
```

Esto creará un entorno virtual y dejará listos los scripts.

---

## 3. Ejecutar los jobs (estilo `npm run`)

Desde la carpeta raíz del proyecto (`CURIOSIDADES`):

```bash
# Ejecutar job1 (equivalente a: python job1/jobspy_search.py)
pipenv run job1

# Ejecutar job2 (equivalente a: python job2/jobfunnel_run.py)
# (depende de la librería externa JobFunnel, que a veces se rompe
# cuando cambian las webs de Indeed/Monster)
pipenv run job2
```

> Piensa en `pipenv run job1` como si fuera `npm run job1`.

### Si `pipenv run job2` muestra mensaje de error de JobFunnel

Ahora mismo JobFunnel tiene bugs conocidos con Monster/Indeed  
(por ejemplo: `Monster Scraper Not Working`, issue #175 en GitHub).

Si ves el mensaje:

> ⚠️  JobFunnel falló al hacer scraping.  
> Tu configuración y tu script están bien; es un problema del scraper.  
> Mientras tanto, usa `job1` que no depende de JobFunnel.

significa que **job2 está bien configurado**, pero la librería externa no
puede scrapear esas webs. En ese caso, usa `pipenv run job1`.

---

## 4. Opción rápida sin Pipenv (no recomendada)

Si no quieres usar Pipenv y ya tienes Python 3.10 y `pip`:

```bash
cd ~/Volumes/Extended/github/CURIOSIDADES
pip install python-jobspy pandas jobfunnel

# Ejecutar job1
python job1/jobspy_search.py

# Ejecutar job2
python job2/jobfunnel_run.py
```

Si tu sistema usa `python3` en lugar de `python`, cambia los comandos por:

```bash
python3 job1/jobspy_search.py
python3 job2/jobfunnel_run.py
```

---

## 5. Resumen corto

1. `cd ~/Volumes/Extended/github/CURIOSIDADES`
2. `pip install pipenv` (solo la primera vez, si no lo tienes).
3. `pipenv install` (solo la primera vez en este proyecto).
4. `pipenv run job1` para el primer buscador.
5. `pipenv run job2` para el segundo buscador.
