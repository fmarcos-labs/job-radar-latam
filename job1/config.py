# =============================================================================
# CONFIGURACIÓN ACTIVA - se guarda en cada CSV para poder iterar
# =============================================================================
CONFIG = {
    "version": "v7.7",
    "paises": ["Chile", "Argentina", "Colombia"],
    "sites_con_remote_flag": ["linkedin"],       # usan is_remote=True
    "sites_con_hours_old": ["indeed"],            # usan hours_old (incompatible con is_remote)
    "sites_eliminados": ["google", "zip_recruiter"],  # no funcionan para Chile/LATAM
    "hours_old": 168,
    "results_wanted": 50,
    "score_minimo": 2,
    "nota": "v7.6: Excluir 'Sr' (abreviatura senior). Excluir 'remote from [pais]' (puesto restringido a otro país). Excluir IoT.",
}

# LinkedIn Chile: 12 queries curadas (las redundantes se eliminaron tras análisis de duplicados)
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
SITES_REMOTE = ["linkedin"]   # soportan is_remote sin conflicto
SITES_HOURS  = ["indeed"]     # requieren hours_old, incompatible con is_remote

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

TOTAL_CALLS = (
    len(QUERIES_LINKEDIN_FULL) +
    len(QUERIES_LINKEDIN_LIGHT) * 2 +
    len(QUERIES_INDEED) * 3
)
