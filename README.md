# GuardrailMap

GuardrailMap is a web-based map for U.S. guardrail terminals and cable barriers. It combines:

- OpenStreetMap (base map + source features via Overpass)
- Mapillary imagery (batch scanning)
- Community reports (registered users can add features, comments, and photos)

Broken installations are highlighted in red.

## Stack (DigitalOcean-friendly)

- **Web/API:** FastAPI + Leaflet
- **Database:** PostgreSQL (recommended: DigitalOcean Managed PostgreSQL)
- **Photo storage:** DigitalOcean Spaces (S3-compatible object storage)
- **Compute:** DigitalOcean App Platform or Droplet workers for ingestion batches

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Environment variables

Create `.env`:

```env
SECRET_KEY=replace-this
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:25060/guardrailmap?sslmode=require
SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
SPACES_REGION=nyc3
SPACES_BUCKET=guardrailmap
SPACES_KEY=DO_SPACES_KEY
SPACES_SECRET=DO_SPACES_SECRET
SPACES_PUBLIC_BASE_URL=https://guardrailmap.nyc3.cdn.digitaloceanspaces.com
MAPILLARY_ACCESS_TOKEN=your_mapillary_token
```

## Data ingestion

### 1) Pull OSM features in batches

```bash
python scripts/fetch_osm_guardrails.py \
  --bbox "24.5,-125,49.4,-66.9" \
  --api-base-url "http://127.0.0.1:8000" \
  --token "<jwt-from-login>"
```

### 2) Scan Mapillary images for likely guardrail/barrier content

```bash
python scripts/mapillary_batch_detect.py \
  --mapillary-token "$MAPILLARY_ACCESS_TOKEN" \
  --bbox "-125,24.5,-66.9,49.4" \
  --api-base-url "http://127.0.0.1:8000" \
  --api-token "<jwt-from-login>" \
  --limit 200
```

The script uses a low-cost heuristic model baseline. Replace with a tiny ONNX model to improve precision.

## Production deployment on DigitalOcean

1. Create Managed PostgreSQL and Spaces bucket.
2. Deploy this repo to App Platform with one web service (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Set the env vars above.
4. Add a worker component for periodic OSM + Mapillary batch jobs.

## API summary

- `POST /api/register`
- `POST /api/login`
- `GET /api/features`
- `POST /api/features` (auth)
- `POST /api/features/{id}/comments` (auth)
- `POST /api/features/{id}/photos` (auth, uploads to Spaces)
