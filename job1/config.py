# =============================================================================
# CONFIGURACIÓN ACTIVA - se guarda en cada CSV para poder iterar
# =============================================================================
CONFIG = {
    "version": "v8.0",
    "paises": ["Chile", "Argentina", "Uruguay", "Peru"],
    "sites_con_remote_flag": ["linkedin"],               # usan is_remote=True
    "sites_con_hours_old": ["indeed", "glassdoor"],      # usan hours_old, incompatible con is_remote
    "sites_eliminados": ["google", "zip_recruiter"],     # no funcionan para LATAM
    "hours_old": 168,
    "results_wanted": 50,
    "score_minimo": 2,
    "nota": "v8.0: Indeed y Glassdoor separados (un fallo de Glassdoor no mata Indeed). LinkedIn solo Chile+AR. Uruguay/Peru solo Indeed+Glassdoor. Filtro LATAM para jobs no-chilenos.",
}

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

CORE_TECH = {
    # JavaScript/TypeScript - stack principal
    "typescript": 4,
    "react": 4,
    "next.js": 4,
    "nextjs": 4,
    "node.js": 4,
    "nodejs": 4,
    "nestjs": 3,
    "express": 3,
    # Python - segunda habilidad fuerte
    "python": 2,
    "django": 2,
    "fastapi": 2,
    # Complementarios
    "graphql": 2,
    "flutter": 2,
}

SECONDARY_TECH = {
    "puppeteer": 1,
    "scraping": 1,
    "strapi": 1,
    "supabase": 1,
    "prisma": 1,
    "postgresql": 1,
    "postgres": 1,
    "websocket": 1,
    "socket.io": 1,
    "api": 1,
    "rest": 1,
    "openai": 2,
}

INCOMPATIBLE_TECH = [
    "elixir", "ruby", "rails", "php", "laravel",
    "java", "c#", ".net", "swift", "kotlin",
    "golang", "go developer", "rust",
    "react native", "dynamics 365", "power apps", "powerbi",
]

EXCLUDE_TITLE_KEYWORDS = [
    # Roles fuera de alcance (seniority / gestión)
    "principal", "staff engineer", "director",
    "head of", "vp of", "cto", "lead",
    "intern", "internship", "práctica", "practica", "practicante", "trainee",
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
    "engineering manager",
    # Tecnologías incompatibles (individual, no frases compuestas)
    "elixir", "golang", "go developer",
    "dynamics 365", "power apps",
    ".net", "c#", "kotlin",
    "ruby", "rails",
    "php", "angular", "drupal",
    "react native",
    "hana",
    "outsystems", "shiny",
    "shopify", "odoo", "moodle",
]

EXCLUDE_COMPANIES = [
    "bairesdev",        # Outsourcing masivo, salarios bajos, no contrata
    "core code io",     # Spam de anuncios genéricos, score siempre 0
    # Ex-empleadores (no volver a postular sin saberlo)
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
]
