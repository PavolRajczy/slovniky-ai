# Docker — mock UI + agentic backend


Dva servisy v `docker-compose.yml`:

1. `backend` — API na porte **8000**
2. `frontend` — UI na porte **8080** (nginx posiela `/api` na backend)

---

### Docker setup

## 1. Kde spustiť príkazy

**Pracovný priečinok musí byť koreň repozitára** — tam, kde leží `docker-compose.yml`


docker version
docker compose version

---

## 2. Príprava `.env`

V koreni repozitára musí byť `.env` s kľúčom OpenAI. Backend bez neho vôbec nenaštartuje.

Ak `.env` ešte nemáš:

```powershell
copy .env.example .env
```

Otvor `.env` a nastav:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://llm.ai.e-infra.cz/v1/
OPENAI_MODEL=mini
OPENAI_MODEL_MINI=mini
OPENAI_EMBEDDING_MODEL=qwen3-embedding-4b
OPENAI_EMBEDDING_DIMENSION=2560
```

Bez úvodzoviek, bez medzier okolo `=`. Kľúč je z chat.ai.e-infra.cz (Účet → API keys), nie z OpenAI cloudu, a do gitu ho nedávaj.

`OPENAI_MODEL` a `OPENAI_MODEL_MINI` sú názvy z katalógu e-INFRA. Predvolený alias `mini` dnes ukazuje na `gpt-oss-120b`. Dá sa zmeniť na `kimi`, `deepseek`, `glm`, `coder` alebo na presný názov modelu. `OPENAI_EMBEDDING_MODEL` je embedding na tom istom endpointe.

Po zmene `.env` kontajner znova postav: `docker compose up --build`. V logu backendu je riadok `LLM API base URL`.

---


Z **toho istého**:

```powershell
docker compose up --build
```

| Čo | Adresa |
| --- | --- |
| UI | http://localhost:8080 |
| API dokumentácia | http://localhost:8000/api/docs |
| Health check | http://localhost:8000/api/health |

Na pozadí (terminál ostane voľný):

```powershell
docker compose up --build -d
```

Zoznam bežiacich kontajnerov:

```powershell
docker compose ps
```

