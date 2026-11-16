from pathlib import Path
import os
# =============================================================================
# CONFIGURACIÓN ACTIVA - se guarda en cada CSV para poder iterar
# =============================================================================
CONFIG = {
    "version": "v10.7",
    "paises": ["Chile", "Argentina", "Uruguay", "Peru"],
    "sites_con_remote_flag": ["linkedin"],               # usan is_remote=True
    "sites_con_hours_old": ["indeed", "glassdoor"],      # usan hours_old, incompatible con is_remote
    "sites_eliminados": ["google", "zip_recruiter"],     # no funcionan para LATAM
    "hours_old": 168,
    "results_wanted": 50,
    "score_minimo": 2,
    "score_fuerte": 20,   # correo HTML: título en negrita y score grande en verde
    "score_medio": 10,    # correo HTML: normal; debajo, gris
    "nota": "v10.0: memoria de vistos (NUEVOS primero), dedupe por titulo+empresa, descripcion de LinkedIn solo para nuevos, remoto de LinkedIn por busqueda (f_WT=2), bypass de titulo solo sin descripcion, sha del commit en email y CSV.",
}

# Descripción de LinkedIn: JobSpy no la baja; se baja SOLO para avisos nuevos (1 request c/u, con sleep).
# Tope duro por corrida: lo que supere queda sin descripción (desc_fetched=0) y pasa por el bypass de título.
MAX_DESC_FETCH = 150

# Memoria de avisos ya mostrados. Vive junto al código en el Mac Mini y el deploy la excluye del rsync.
SEEN_FILENAME = "seen.json"
EMAIL_SUBJECT_PREFIX = "⭐ Job Radar LATAM"
CLICKS_FILE = os.environ.get("RADAR_CLICKS_FILE", str(Path(__file__).parent / "clicks.json"))   # lo escribe job1/redirector.py

# LinkedIn Chile: 18 queries (stack completo + español + AI)
QUERIES_LINKEDIN_FULL = [
    "fullstack developer typescript",
    "react developer",
    "nodejs developer",
    "python developer",
    "flutter developer",
    "remote developer latam",
    "backend developer",
    "frontend developer",
    "ingeniero fullstack",
    "desarrollador fullstack",
    "desarrollador react",
    "desarrollador freelance",
    "ai developer",
    "nextjs developer",
    "nestjs developer",
    "desarrollador backend",
    "typescript developer",
    "desarrollador typescript",
    # Nuevas — stack específico
    "desarrollador full stack javascript",
    "full stack developer react node",
    "backend developer node.js",
    "desarrollador backend node",
    "desarrollador backend nestjs",
    "desarrollador frontend react",
    "react js developer",
    "desarrollador flutter",
    "python junior",
]

# LinkedIn Argentina/Colombia: 6 queries genéricas que cubren el espectro más amplio
QUERIES_LINKEDIN_LIGHT = [
    "fullstack developer typescript",
    "react developer",
    "backend developer",
    "remote developer latam",
    "desarrollador fullstack",
    "ingeniero fullstack",
]

# Indeed: todas las queries (rápido ~1s/call, sin riesgo de ban)
QUERIES_INDEED = [
    "fullstack developer typescript",
    "react developer",
    "nextjs developer",
    "frontend developer typescript",
    "nodejs developer",
    "python developer",
    "django developer",
    "fastapi developer",
    "backend python developer",
    "flutter developer",
    "remote developer latam",
    "fullstack remote latam",
    "react remote latam",
    "senior fullstack developer",
    "graphql developer",
    "backend developer",
    "frontend developer",
    "ai engineer",
    "ai developer",
    "ingeniero backend",
    "ingeniero fullstack",
    "desarrollador backend",
    "desarrollador fullstack",
    "desarrollador python",
    "desarrollador react",
    "freelance developer",
    "fullstack freelance",
    "desarrollador freelance",
]

# Solo Indeed y LinkedIn (Google y ZipRecruiter no funcionan para LATAM)
SITES_REMOTE = ["linkedin"]               # soportan is_remote sin conflicto
SITES_HOURS  = ["indeed", "glassdoor"]    # requieren hours_old, incompatible con is_remote

# Salud de la corrida (job1/salud.py): el correo muestra las filas crudas de cada fuente esperada.
# Solo las esenciales avisan al quedar en 0. Glassdoor no: 0 filas aprobadas en 708 corridas (medido 15-11),
# y un aviso que sale siempre deja de leerse.
FUENTES_ESPERADAS = [*SITES_REMOTE, *SITES_HOURS, "getonbrd"]
FUENTES_ESENCIALES = ["linkedin", "indeed", "getonbrd"]
# Corre 2 veces al día y el hueco normal más largo es de ~17 h; pasado este tope el correo dice desde cuándo no hay datos.
MAX_HORAS_ENTRE_CORRIDAS = 26

CORE_TECH = {
    # JavaScript/TypeScript - stack principal
    "javascript": 4,   # fix: "Fullstack JavaScript Developer" scoreaba 0 sin esta key
    "typescript": 4,
    "react": 4,
    "next.js": 4,
    "nextjs": 4,
    "node": 4,   # cubre node.js/nodejs/"Node js"/"Node OR .NET" (token seguro, verificado en 117 corridas)
    "nestjs": 3,
    "express": 3,
    # Python - segunda habilidad fuerte (fastapi = uso real en backends IA)
    "python": 2,
    "django": 2,
    "fastapi": 3,
    # Complementarios
    "graphql": 2,
    "flutter": 2,
}

# IA / LLM - carril emergente (inbound real: "Fullstack IA" Muck/IBM).
# Peso 3 (no 4): "fullstack + IA" flota al tope sin que un rol AI/ML puro domine el core.
# Solo tokens multi-palabra seguros: NADA de "ia"/"ai"/"rag" sueltos (matchean media/training/storage).
AI_TECH = {
    "openai": 3,
    "langchain": 3,
    "llm": 3,
    "genai": 3,
    "generative ai": 3,
    "chatbot": 3,
    "ai engineer": 3,
    "ai developer": 3,
    "ai agent": 3,
    "agentes ia": 3,
    "fullstack ia": 3,
    "inteligencia artificial": 3,
    "artificial intelligence": 3,
    "machine learning": 2,
    "prompt engineering": 2,
    "vector database": 2,
}

SECONDARY_TECH = {
    "puppeteer": 1,
    "scraping": 1,
    "strapi": 1,
    "supabase": 1,
    "prisma": 1,
    "postgres": 1,   # "postgres" ya cubre "postgresql" (evita doble-conteo)
    "mysql": 1,       # demanda 57 en postings + CChC BD-heavy
    "mongodb": 1,     # demanda 35 + 3 procesos reales (USS/ATCOM/Falabella-HUB)
    "mongoose": 1,
    "websocket": 1,
    "socket.io": 1,
    "api": 1,
    "rest": 1,
}

# Cloud / arquitectura - alta demanda (AWS=219 postings) + probado real.
# Abre roles cloud-fullstack de mayor banda salarial. Peso alto solo donde convertís.
PLATFORM_TECH = {
    "aws": 3,             # Lambda/S3/API Gateway/SES reales (Depot, GeoTrans)
    "serverless": 2,      # GeoTrans (Lambda + API Gateway), Depot
    "microservices": 2,   # Depot (scraper desacoplado), JL (microservicio reportes)
    "microservicios": 2,
}

INCOMPATIBLE_TECH = [
    "elixir", "ruby", "rails", "php", "laravel",
    "c#", ".net", "swift", "kotlin",  # "java" removido: el filtro de titulos ya excluye \bjava\b(?!script) antes del scoring; aqui solo penalizaba "javascript"
    "golang", "rust",  # "go developer" removido: substring de "django developer" (ver regex en helpers)
    "react native", "dynamics 365", "power apps", "powerbi",
]

EXCLUDE_TITLE_KEYWORDS = [
    # Roles fuera de alcance (seniority / gestión)
    "principal", "director", "chief",
    "architect", "arquitect", "manager", "experto",
    "head of", "vp of", "lead",  # "cto" removido: substring mataba Contractor/Proyecto/Sector/Arquitecto (ver regex \bcto\b en helpers)
    "práctica", "practica", "practicante", "trainee",  # "intern"/"internship" movidos a regex \bintern\b en helpers (mataban "International")
    # Tecnologías / dominios fuera del stack
    "iot",
    # Roles no-dev que contaminan resultados
    "qa", "quality assurance", "automation engineer",
    "designer", "ui/ux", "ux/ui",
    "data analyst", "data engineer", "data science", "data scientist",
    "devops", "sre", "site reliability",
    "salesforce", "apex",
    "support engineer", "technical support",
    "observability", "migration consultant", "upgrade consultant",
    # Tecnologías incompatibles (individual, no frases compuestas)
    # RECALL: lenguajes backend (.net/java/php/go/ruby/kotlin/elixir/rust) NO se excluyen aca:
    # suman 0 puntos -> job puro de esos cae solo por score_minimo, y "Node OR .NET" sobrevive por Node.
    # Solo quedan: plataformas cerradas + "react native" (scorea alto por "react" pero es mobile, el score no lo filtra).
    "dynamics 365", "power apps",
    "drupal",
    "react native",
    "hana",
    "outsystems", "shiny",
    "shopify", "odoo", "moodle",
]

EXCLUDE_COMPANIES = [
    "bairesdev",        # Outsourcing masivo, salarios bajos, no contrata
    "core code io",     # Spam de anuncios genéricos, score siempre 0
    # Ex-empleadores (no volver a postular sin saberlo). Fuente: resume.json work[] (api.resume), 03-11-2026
    "siigsa",
    "tipddy",
    "jl ltda",
    "j.l. ltda",
    "klog",
    "depot group",
    "depotgroup",
    "depot chile",
    "grupo mil sabores",
    "grupo los robles",
    "dotsolution",
]

# LinkedIn: solo Chile (FULL) + Argentina (LIGHT)
# Indeed: 4 países × todas las queries (calls independientes)
# Glassdoor: 4 países × todas las queries (calls independientes, si falla no afecta Indeed)
TOTAL_CALLS = (
    len(QUERIES_LINKEDIN_FULL) * 1 +        # Chile LinkedIn
    len(QUERIES_LINKEDIN_LIGHT) * 1 +       # Argentina LinkedIn
    len(QUERIES_INDEED) * 4 * len(SITES_HOURS)  # 4 países × 2 sitios separados
)

# Keywords para filtrar jobs de países no-chilenos:
# solo pasan si la descripción/título indica apertura a LATAM o región
LATAM_KEYWORDS = [
    "latam", "latin america", "latinoamérica", "latinoamerica",
    "latin-america", "south america", "sudamérica", "sudamerica",
    "remote latam", "latam remote", "toda latinoamérica",
    "toda latinoamerica", "cualquier país", "cualquier pais",
    "open to all", "anywhere in latam", "worldwide", "global remote",
    "chile",  # el job menciona chile explícitamente
    "americas", "américa latina", "america latina",  # "Node/TS/Python | Americas, Remote" moria por este filtro
]
