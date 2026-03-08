"""Fetch guardrail/cable barrier points from OpenStreetMap Overpass and push into API."""

import argparse

import httpx

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

OVERPASS_QUERY = """
[out:json][timeout:180];
(
  node["barrier"="guard_rail"]({south},{west},{north},{east});
  node["barrier"="cable_barrier"]({south},{west},{north},{east});
  node["guardrail_terminal"]({south},{west},{north},{east});
);
out body;
"""


def fetch_osm_points(bbox: tuple[float, float, float, float]) -> list[dict]:
    south, west, north, east = bbox
    query = OVERPASS_QUERY.format(south=south, west=west, north=north, east=east)
    response = httpx.post(OVERPASS_URL, data=query, timeout=240)
    response.raise_for_status()
    data = response.json()
    points = []
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        points.append(
            {
                'latitude': element['lat'],
                'longitude': element['lon'],
                'feature_type': tags.get('barrier', 'guardrail_terminal'),
                'is_broken': tags.get('broken') == 'yes',
                'source': 'osm',
                'source_ref': f"osm:{element['id']}",
            }
        )
    return points


def publish_points(api_base_url: str, token: str, points: list[dict]):
    headers = {'Authorization': f'Bearer {token}'}
    with httpx.Client(base_url=api_base_url, headers=headers, timeout=20) as client:
        for point in points:
            client.post('/api/features', json=point)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox', required=True, help='south,west,north,east')
    parser.add_argument('--api-base-url', required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()

    bbox = tuple(float(v) for v in args.bbox.split(','))
    points = fetch_osm_points(bbox)
    print(f'Fetched {len(points)} OSM points')
    publish_points(args.api_base_url, args.token, points)
    print('Published points to API')
