"""Batch Mapillary image scan with low-cost heuristic detection.

This script uses Mapillary API for image discovery and a simple edge-density heuristic
as a placeholder cheap model to flag likely guardrail/barrier images.
Swap `is_guardrail_like` with a tiny ONNX model for better precision.
"""

import argparse
from io import BytesIO

import httpx
import numpy as np
from PIL import Image


def list_mapillary_images(token: str, bbox: str, limit: int) -> list[dict]:
    url = 'https://graph.mapillary.com/images'
    params = {
        'access_token': token,
        'fields': 'id,thumb_1024_url,geometry',
        'bbox': bbox,
        'limit': limit,
    }
    res = httpx.get(url, params=params, timeout=60)
    res.raise_for_status()
    return res.json().get('data', [])


def is_guardrail_like(image_bytes: bytes) -> tuple[bool, float]:
    img = Image.open(BytesIO(image_bytes)).convert('L').resize((256, 256))
    arr = np.array(img, dtype=np.float32)
    gx = np.abs(np.diff(arr, axis=1)).mean()
    gy = np.abs(np.diff(arr, axis=0)).mean()
    score = float((gx * 0.65 + gy * 0.35) / 255)
    return score > 0.18, score


def push_detection(api_base_url: str, token: str, lat: float, lon: float, score: float):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'latitude': lat,
        'longitude': lon,
        'feature_type': 'guardrail_or_cable_barrier',
        'is_broken': False,
        'source': 'mapillary',
        'confidence': score,
    }
    httpx.post(f'{api_base_url}/api/features', json=payload, headers=headers, timeout=20)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mapillary-token', required=True)
    parser.add_argument('--bbox', required=True, help='west,south,east,north')
    parser.add_argument('--api-base-url', required=True)
    parser.add_argument('--api-token', required=True)
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()

    images = list_mapillary_images(args.mapillary_token, args.bbox, args.limit)
    print(f'Loaded {len(images)} Mapillary images')

    for image in images:
        thumb_url = image.get('thumb_1024_url')
        if not thumb_url:
            continue
        img_res = httpx.get(thumb_url, timeout=30)
        if img_res.status_code != 200:
            continue

        match, score = is_guardrail_like(img_res.content)
        if not match:
            continue

        coords = image.get('geometry', {}).get('coordinates', [None, None])
        lon, lat = coords[0], coords[1]
        if lat is None or lon is None:
            continue
        push_detection(args.api_base_url, args.api_token, lat, lon, score)

    print('Batch detection complete')
