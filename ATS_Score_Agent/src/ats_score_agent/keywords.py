"""Canonical skills and aliases used for ATS-style keyword matching."""

from __future__ import annotations

import re

# canonical term -> accepted surface forms
SKILL_ALIASES: dict[str, frozenset[str]] = {
    "python": frozenset({"python", "py"}),
    "javascript": frozenset({"javascript", "js", "ecmascript"}),
    "typescript": frozenset({"typescript", "ts"}),
    "java": frozenset({"java"}),
    "c++": frozenset({"c++", "cpp", "cplusplus"}),
    "c#": frozenset({"c#", "csharp", "c sharp"}),
    "go": frozenset({"go", "golang"}),
    "rust": frozenset({"rust"}),
    "ruby": frozenset({"ruby"}),
    "php": frozenset({"php"}),
    "swift": frozenset({"swift"}),
    "kotlin": frozenset({"kotlin"}),
    "scala": frozenset({"scala"}),
    "sql": frozenset({"sql"}),
    "nosql": frozenset({"nosql"}),
    "html": frozenset({"html", "html5"}),
    "css": frozenset({"css", "css3"}),
    "react": frozenset({"react", "reactjs", "react.js"}),
    "react native": frozenset({"react native", "react-native"}),
    "angular": frozenset({"angular", "angularjs"}),
    "vue": frozenset({"vue", "vuejs", "vue.js"}),
    "next.js": frozenset({"next.js", "nextjs", "next js"}),
    "node.js": frozenset({"node.js", "nodejs", "node js", "node"}),
    "express": frozenset({"express", "express.js", "expressjs"}),
    "django": frozenset({"django"}),
    "flask": frozenset({"flask"}),
    "fastapi": frozenset({"fastapi"}),
    "spring": frozenset({"spring", "spring boot", "springboot"}),
    "graphql": frozenset({"graphql"}),
    "rest": frozenset({"rest", "restful", "rest api", "rest apis"}),
    "grpc": frozenset({"grpc", "g rpc"}),
    "aws": frozenset({"aws", "amazon web services"}),
    "azure": frozenset({"azure", "microsoft azure"}),
    "gcp": frozenset({"gcp", "google cloud", "google cloud platform"}),
    "docker": frozenset({"docker"}),
    "kubernetes": frozenset({"kubernetes", "k8s"}),
    "terraform": frozenset({"terraform"}),
    "ci/cd": frozenset({"ci/cd", "cicd", "continuous integration", "continuous delivery"}),
    "github actions": frozenset({"github actions", "github action"}),
    "jenkins": frozenset({"jenkins"}),
    "linux": frozenset({"linux"}),
    "git": frozenset({"git"}),
    "postgres": frozenset({"postgres", "postgresql", "psql"}),
    "mysql": frozenset({"mysql"}),
    "mongodb": frozenset({"mongodb", "mongo"}),
    "redis": frozenset({"redis"}),
    "elasticsearch": frozenset({"elasticsearch", "elastic search"}),
    "kafka": frozenset({"kafka", "apache kafka"}),
    "spark": frozenset({"spark", "apache spark", "pyspark"}),
    "hadoop": frozenset({"hadoop"}),
    "airflow": frozenset({"airflow", "apache airflow"}),
    "pandas": frozenset({"pandas"}),
    "numpy": frozenset({"numpy"}),
    "scikit-learn": frozenset({"scikit-learn", "sklearn", "scikit learn"}),
    "tensorflow": frozenset({"tensorflow"}),
    "pytorch": frozenset({"pytorch", "torch"}),
    "machine learning": frozenset({"machine learning", "ml"}),
    "deep learning": frozenset({"deep learning"}),
    "nlp": frozenset({"nlp", "natural language processing"}),
    "llm": frozenset({"llm", "large language model", "large language models"}),
    "prompt engineering": frozenset({"prompt engineering", "prompt engineer"}),
    "rag": frozenset({"rag", "retrieval augmented generation"}),
    "data analysis": frozenset({"data analysis", "data analytics"}),
    "data visualization": frozenset({"data visualization", "data viz"}),
    "tableau": frozenset({"tableau"}),
    "power bi": frozenset({"power bi", "powerbi"}),
    "excel": frozenset({"excel", "microsoft excel"}),
    "looker": frozenset({"looker"}),
    "snowflake": frozenset({"snowflake"}),
    "databricks": frozenset({"databricks"}),
    "dbt": frozenset({"dbt"}),
    "etl": frozenset({"etl", "elt"}),
    "agile": frozenset({"agile"}),
    "scrum": frozenset({"scrum"}),
    "kanban": frozenset({"kanban"}),
    "jira": frozenset({"jira"}),
    "confluence": frozenset({"confluence"}),
    "product management": frozenset({"product management", "product manager"}),
    "project management": frozenset({"project management", "project manager"}),
    "stakeholder management": frozenset({"stakeholder management", "stakeholders"}),
    "roadmap": frozenset({"roadmap", "roadmaps", "product roadmap"}),
    "user research": frozenset({"user research", "ux research"}),
    "figma": frozenset({"figma"}),
    "ux": frozenset({"ux", "user experience"}),
    "ui": frozenset({"ui", "user interface"}),
    "a/b testing": frozenset({"a/b testing", "ab testing", "split testing"}),
    "seo": frozenset({"seo", "search engine optimization"}),
    "google analytics": frozenset({"google analytics", "ga4"}),
    "salesforce": frozenset({"salesforce"}),
    "hubspot": frozenset({"hubspot"}),
    "excel modeling": frozenset({"financial modeling", "excel modeling"}),
    "forecasting": frozenset({"forecasting", "forecast"}),
    "budgeting": frozenset({"budgeting", "budget management"}),
    "communication": frozenset({"communication", "written communication", "verbal communication"}),
    "leadership": frozenset({"leadership", "people management", "team leadership"}),
    "cross-functional": frozenset({"cross-functional", "cross functional", "crossfunctional"}),
    "problem solving": frozenset({"problem solving", "problem-solving"}),
    "customer success": frozenset({"customer success", "customer support"}),
    "saas": frozenset({"saas"}),
    "b2b": frozenset({"b2b"}),
    "api": frozenset({"api", "apis"}),
    "microservices": frozenset({"microservices", "micro-services", "microservice"}),
    "system design": frozenset({"system design", "distributed systems"}),
    "testing": frozenset({"testing", "qa", "quality assurance", "unit testing", "integration testing"}),
    "pytest": frozenset({"pytest"}),
    "selenium": frozenset({"selenium"}),
    "playwright": frozenset({"playwright"}),
    "cypress": frozenset({"cypress"}),
    "security": frozenset({"security", "infosec", "cybersecurity", "application security"}),
    "oauth": frozenset({"oauth", "oauth2", "oauth 2.0"}),
    "sso": frozenset({"sso", "single sign-on", "single sign on"}),
    "observability": frozenset({"observability", "monitoring", "logging"}),
    "datadog": frozenset({"datadog"}),
    "splunk": frozenset({"splunk"}),
    "pagerduty": frozenset({"pagerduty"}),
    "okta": frozenset({"okta"}),
    "webpack": frozenset({"webpack"}),
    "vite": frozenset({"vite"}),
    "tailwind": frozenset({"tailwind", "tailwindcss"}),
    "redux": frozenset({"redux"}),
    "django rest framework": frozenset({"django rest framework", "drf"}),
    "pandas": frozenset({"pandas"}),
}

STOPWORDS = frozenset(
    """
    a an the and or of to for in on with from by as at is are was were be been being
    this that those these it its you your we our they their he she his her
    will would should could may might must need needs needed
    including include includes included such than then also both either neither
    into over under about after before during without within across
    job role team teams company work working works worked
    experience experienced strong ability able using use used uses
    required require requirements requirement preferred prefer
    plus min minimum years year yr yrs
    other others well new high highly
    candidate candidates applicant applicants
    responsibilities responsibility duties duty
    description summary overview position
    """.split()
)

DEGREE_TERMS = {
    "bachelor": frozenset({"bachelor", "bachelors", "bs", "ba", "b.s", "b.a", "undergraduate"}),
    "master": frozenset({"master", "masters", "ms", "ma", "m.s", "mba", "m.b.a"}),
    "phd": frozenset({"phd", "ph.d", "doctorate", "doctoral"}),
}

SECTION_HEADERS = {
    "summary": frozenset({"summary", "profile", "objective", "about"}),
    "skills": frozenset({"skills", "technical skills", "core competencies", "technologies"}),
    "experience": frozenset({"experience", "work experience", "employment", "professional experience"}),
    "education": frozenset({"education", "academic", "academics"}),
    "certifications": frozenset({"certifications", "certificates", "licenses"}),
    "projects": frozenset({"projects", "selected projects"}),
}


def normalize_text(text: str) -> str:
    lowered = text.lower().replace("–", "-").replace("—", "-")
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[/\\]", " ", lowered)
    lowered = re.sub(r"[^a-z0-9+#.\s-]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def alias_lookup() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        mapping[normalize_text(canonical)] = canonical
        for alias in aliases:
            mapping[normalize_text(alias)] = canonical
    return mapping
