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
```

Bez úvodzoviek, bez medzier okolo `=`. Kľúč si každý dá vlastný — do gitu ho nedávaj.

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

