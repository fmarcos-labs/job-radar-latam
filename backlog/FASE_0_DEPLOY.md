# FASE 0: Deploy en Railway

**Status**: ⏸️ PENDIENTE
**Prioridad**: Alta
**Dependencias**: ninguna

---

## Contexto

El script v7.7 ya tiene todo lo necesario para correr en Railway:
- `railway.toml` — cron lunes y jueves 9am UTC-3 (12pm UTC)
- `send_email_report()` — envía `results.md` al Gmail al terminar

Railway usa **Nixpacks** para auto-detectar Python + Pipfile automáticamente.
No se necesita Dockerfile.

Los resultados **no se persisten** en Railway (no hay filesystem entre runs).
El email es la única forma de conservarlos — y es suficiente.

---

## Tareas

### Tarea 0.1: Crear repo privado en GitHub

- Qué hacer:
  1. Ir a github.com → New repository
  2. Nombre: `job-radar-latam` (privado)
  3. Sin README, sin .gitignore (ya existen localmente)
  4. Copiar la URL del repo recién creado

### Tarea 0.2: Subir código a GitHub

- Archivos a incluir:
  - `job1/jobspy_search.py`
  - `railway.toml`
  - `Pipfile`
  - `.gitignore`
  - `CLAUDE.md`
  - `README.md`
  - `job1/manual_sources.json`
  - `backlog/` (esta carpeta)
- Archivos excluidos por `.gitignore`: carpetas de runs `job1/20*/`, `Pipfile.lock`, `.env`
- Comandos (reemplazar URL por la del repo creado):
  ```bash
  git remote add origin https://github.com/TU_USER/job-radar-latam.git
  git push -u origin master
  ```

### Tarea 0.3: Configurar Gmail App Password

- Qué hacer:
  1. Ir a myaccount.google.com → Seguridad
  2. Activar verificación en 2 pasos (si no está activa)
  3. Buscar "Contraseñas de aplicación"
  4. Crear nueva → categoría "Correo" → dispositivo "Otro (nombre personalizado)" → "jobspy"
  5. Copiar los 16 caracteres generados (solo se muestran una vez)

### Tarea 0.4: Crear proyecto en Railway y conectar repo

- Qué hacer:
  1. Ir a railway.app → New Project
  2. "Deploy from GitHub repo" → seleccionar el repo creado
  3. Railway detecta Python + Pipfile automáticamente con Nixpacks (sin configuración extra)
  4. En la pestaña "Variables" del proyecto, agregar:
     - `GMAIL_USER` = tu email (ej: `freddy@gmail.com`)
     - `GMAIL_APP_PASSWORD` = los 16 caracteres del paso anterior
  5. El cron en `railway.toml` se activa automáticamente

### Tarea 0.5: Verificar el deploy

- Qué hacer:
  1. En Railway → pestaña "Deployments" → buscar opción de trigger manual del cron
  2. Ejecutar manualmente (el run toma ~15 minutos)
  3. Revisar logs en tiempo real en Railway
  4. Al terminar: chequear bandeja de entrada del Gmail
  5. El email debe tener asunto: `[JobSpy] XX trabajos encontrados — YYYYMMDD_HHMM`
  6. El cuerpo debe ser el contenido completo de `results.md`

---

## Criterios de Aceptación

- [ ] Repo privado creado en GitHub con el código subido
- [ ] Variables `GMAIL_USER` y `GMAIL_APP_PASSWORD` configuradas en Railway
- [ ] Primer run manual completado sin errores en los logs de Railway
- [ ] Email recibido en Gmail con los resultados
- [ ] Cron activo (Railway muestra próxima ejecución programada)
