# physense-api

FastAPI backend for the [Physense](https://physense.tampipo.fr) platform. Exposes physics simulations from `physense-qm` (and future modules) as an HTTP/WebSocket API.

Live at: **https://api.physense.tampipo.fr**  
Interactive docs: **https://api.physense.tampipo.fr/docs**

---

## Structure

```
src/physense_api/
  main.py              # FastAPI app, CORS, lifespan
  routers/
    qm.py              # /qm/eigenstates (POST), /qm/evolve (WebSocket)
  schemas/
    qm.py              # Pydantic request/response models
  utils/
    potentials.py      # Maps PotentialSchema → physense_qm Potential objects
```

---

## Running locally

```bash
git clone https://github.com/Tampipo/physense-api
cd physense-api
pip install -e ".[dev]"
uvicorn physense_api.main:app --reload --port 8000
```

CORS is configured via the `ALLOWED_ORIGINS` environment variable (comma-separated). Defaults to `http://localhost:3000` for local development.

```bash
ALLOWED_ORIGINS=http://localhost:3000,https://physense.tampipo.fr uvicorn physense_api.main:app
```

---

## Running with Docker

```bash
docker build -t physense-api .
docker run -p 8000:8000 -e ALLOWED_ORIGINS=http://localhost:3000 physense-api
```

---

## API reference

### `POST /qm/eigenstates`

Solves the time-independent Schrödinger equation and returns eigenstates.

**Request:**

```json
{
  "grid": { "x_min": -8, "x_max": 8, "n_points": 512 },
  "potential": {
    "type": "harmonic",
    "params": { "omega": 1.0, "x0": 0.0 }
  },
  "n_states": 5
}
```

**Potential types (Option A):** `free`, `harmonic`, `infinite_well`, `finite_well`, `barrier`, `step`, `double_well`

**Custom potential (Option B):** pass `type: "custom"` and a `values` array of length `n_points` :

```json
{
  "potential": {
    "type": "custom",
    "values": [0.0, 0.1, 0.5, ...]
  }
}
```

**Response:**

```json
{
  "x": [...],
  "potential": [...],
  "energies": [0.5, 1.5, 2.5, 3.5, 4.5],
  "wavefunctions": [[...], [...], ...],
  "n_states": 5
}
```

---

### `WS /qm/evolve`

Streams wavepacket time evolution frames.

**Protocol:**

1. Client connects to `ws://host/qm/evolve`
2. Client sends `EvolveRequest` as JSON
3. Server sends `{ "type": "metadata", "x": [...], "potential": [...], ... }`
4. Server streams `{ "type": "frame", "frame": i, "t": 0.1, "probability_density": [...], "norm": 1.0 }`
5. Server sends `{ "type": "done" }`

**Request:**

```json
{
  "grid": { "x_min": -20, "x_max": 20, "n_points": 512 },
  "potential": { "type": "barrier", "params": { "height": 2.0, "width": 2.0 } },
  "wavepacket": { "x0": -8.0, "k0": 1.5, "sigma": 1.5 },
  "t_max": 10.0,
  "dt": 0.005,
  "n_frames": 80
}
```

**Example (Python):**

```python
import asyncio, websockets, json

async def test():
    async with websockets.connect("wss://api.physense.tampipo.fr/qm/evolve") as ws:
        await ws.send(json.dumps({
            "grid": {"x_min": -20, "x_max": 20, "n_points": 512},
            "potential": {"type": "barrier", "params": {"height": 2.0, "width": 2.0}},
            "wavepacket": {"x0": -8.0, "k0": 1.5, "sigma": 1.5},
            "t_max": 10.0, "dt": 0.005, "n_frames": 60,
        }))
        async for msg in ws:
            data = json.loads(msg)
            print(data["type"], data.get("t", ""))
            if data["type"] == "done":
                break

asyncio.run(test())
```

---

## Limits

| Parameter | Min | Max |
|---|---|---|
| `n_points` | 64 | 2048 |
| `n_states` | 1 | 20 |
| `n_frames` | 10 | 200 |
| `t_max` | — | 50.0 |
| `dt` | — | 0.1 |

---

## Exporting the OpenAPI schema

```bash
pip install pyyaml
python scripts/export_openapi.py
```

Outputs `openapi.yaml` at the project root, consumed by `orval` in the frontend to generate TypeScript clients.

---

## Running tests

```bash
pytest
```

---

## Deployment

The API is containerised and deployed on a k3s cluster via ArgoCD. The CI pipeline (GitHub Actions) builds and pushes a multi-arch Docker image to GHCR on every push to `main`. ArgoCD Image Updater automatically bumps the image tag in the gitops repo and triggers a rollout.

```
push to main → CI → ghcr.io/tampipo/physense-api:x.y.z → ArgoCD → k3s
```

---

## Dependencies

- `fastapi >= 0.115`
- `uvicorn >= 0.30`
- `websockets >= 13.0`
- `physense-utils`
- `physense-qm`
