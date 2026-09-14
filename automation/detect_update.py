"""Detect whether new usable satellite data is available for Bengaluru.

This script is read-only:
- does NOT modify the historical atlas
- does NOT retrain models
- does NOT overwrite website data
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import ee
import google.auth


BENGALURU_BOUNDS = [
    77.4459721532,
    12.7919511319,
    77.7501879705,
    13.1512756019,
]

COLLECTIONS = {
    "landsat8": {
        "id": "LANDSAT/LC08/C02/T1_L2",
        "cloud_field": "CLOUD_COVER",
        "cloud_limit": 20,
    },
    "sentinel2": {
        "id": "COPERNICUS/S2_SR_HARMONIZED",
        "cloud_field": "CLOUDY_PIXEL_PERCENTAGE",
        "cloud_limit": 20,
    },
}


def iso_from_millis(value):
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def latest_usable_image(collection_id, cloud_field, cloud_limit, region):
    collection = (
        ee.ImageCollection(collection_id)
        .filterBounds(region)
        .filter(ee.Filter.lt(cloud_field, cloud_limit))
        .sort("system:time_start", False)
    )

    image = collection.first()

    info = ee.Algorithms.If(
        image,
        ee.Dictionary({
            "time": image.get("system:time_start"),
            "cloud": image.get(cloud_field),
            "id": image.get("system:index"),
        }),
        None,
    )

    return ee.Dictionary(info).getInfo() if info else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        default=os.environ.get("EE_PROJECT_ID"),
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path("automation/update_state.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("update-status.json"),
    )
    args = parser.parse_args()

    if not args.project:
        parser.error("Set EE_PROJECT_ID or use --project")

    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/cloud-platform",
        ]
    )

    ee.Initialize(
        credentials=credentials,
        project=args.project,
    )

    region = ee.Geometry.Rectangle(
        BENGALURU_BOUNDS,
        geodesic=False,
    )

    if args.state.exists():
        state = json.loads(args.state.read_text(encoding="utf-8"))
    else:
        state = {}

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "kind": "usable_update_detection",
        "updates_available": False,
        "collections": {},
    }

    for name, config in COLLECTIONS.items():
        latest = latest_usable_image(
            config["id"],
            config["cloud_field"],
            config["cloud_limit"],
            region,
        )

        if latest:
            latest_time = iso_from_millis(latest["time"])
            previous_time = state.get(name)

            is_new = previous_time is None or latest_time > previous_time

            result["collections"][name] = {
                "collection": config["id"],
                "latest_usable_acquisition": latest_time,
                "cloud_percentage": latest["cloud"],
                "image_id": latest["id"],
                "previous_processed_acquisition": previous_time,
                "update_available": is_new,
            }

            if is_new:
                result["updates_available"] = True

        else:
            result["collections"][name] = {
                "collection": config["id"],
                "latest_usable_acquisition": None,
                "update_available": False,
            }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()