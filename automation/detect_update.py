"""Detect whether new usable satellite data is available for Bengaluru.

Read-only detector:
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

MAX_AOI_CLOUD_PERCENT = 20.0

COLLECTIONS = {
    "landsat8": {
        "id": "LANDSAT/LC08/C02/T1_L2",
        "scene_cloud_field": "CLOUD_COVER",
        "scene_cloud_limit": 30,
        "type": "landsat",
    },
    "sentinel2": {
        "id": "COPERNICUS/S2_SR_HARMONIZED",
        "scene_cloud_field": "CLOUDY_PIXEL_PERCENTAGE",
        "scene_cloud_limit": 30,
        "type": "sentinel2",
    },
}


def iso_from_millis(value):
    if value is None:
        return None
    return datetime.fromtimestamp(
        value / 1000,
        tz=timezone.utc
    ).isoformat()


def landsat_clear_mask(image):
    qa = image.select("QA_PIXEL")

    cloud = qa.bitwiseAnd(1 << 3).neq(0)
    shadow = qa.bitwiseAnd(1 << 4).neq(0)

    clear = cloud.Or(shadow).Not()

    return clear.rename("clear")


def sentinel_clear_mask(image):
    scl = image.select("SCL")

    # Sentinel-2 Scene Classification Layer
    bad = (
        scl.eq(3)   # cloud shadow
        .Or(scl.eq(8))   # cloud medium probability
        .Or(scl.eq(9))   # cloud high probability
        .Or(scl.eq(10))  # thin cirrus
        .Or(scl.eq(11))  # snow/ice
    )

    return bad.Not().rename("clear")


def calculate_aoi_clear_percent(image, satellite_type, region):
    if satellite_type == "landsat":
        clear_mask = landsat_clear_mask(image)
        scale = 30
    else:
        clear_mask = sentinel_clear_mask(image)
        scale = 20

    result = clear_mask.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e8,
        bestEffort=True,
    )

    clear_fraction = result.get("clear")

    clear_fraction = ee.Number(
        ee.Algorithms.If(
            clear_fraction,
            clear_fraction,
            0
        )
    )

    return clear_fraction.multiply(100)


def inspect_latest_candidates(config, region):
    collection = (
        ee.ImageCollection(config["id"])
        .filterBounds(region)
        .filter(
            ee.Filter.lt(
                config["scene_cloud_field"],
                config["scene_cloud_limit"],
            )
        )
        .sort("system:time_start", False)
        .limit(10)
    )

    image_list = collection.toList(10)
    count = collection.size().getInfo()

    candidates = []

    for index in range(count):
        image = ee.Image(image_list.get(index))

        acquisition_ms = image.get("system:time_start").getInfo()
        acquisition = iso_from_millis(acquisition_ms)

        scene_cloud = image.get(
            config["scene_cloud_field"]
        ).getInfo()

        image_id = image.get("system:index").getInfo()

        clear_percent = (
            calculate_aoi_clear_percent(
                image,
                config["type"],
                region,
            ).getInfo()
        )

        cloud_percent_aoi = 100.0 - clear_percent

        candidates.append({
            "image_id": image_id,
            "acquisition": acquisition,
            "scene_cloud_percentage": scene_cloud,
            "aoi_clear_percentage": round(clear_percent, 2),
            "aoi_cloud_percentage": round(cloud_percent_aoi, 2),
            "usable": cloud_percent_aoi <= MAX_AOI_CLOUD_PERCENT,
        })

    return candidates


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
        parser.error(
            "Set EE_PROJECT_ID or use --project."
        )

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
        state = json.loads(
            args.state.read_text(encoding="utf-8")
        )
    else:
        state = {}

    result = {
        "checked_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "kind": "usable_update_detection_v2",

        "max_aoi_cloud_percent":
            MAX_AOI_CLOUD_PERCENT,

        "updates_available": False,

        "collections": {},
    }

    for name, config in COLLECTIONS.items():

        candidates = inspect_latest_candidates(
            config,
            region,
        )

        previous = state.get(name)

        selected = None

        for candidate in candidates:

            if not candidate["usable"]:
                continue

            if (
                previous is None
                or candidate["acquisition"] > previous
            ):
                selected = candidate
                break

        result["collections"][name] = {
            "collection": config["id"],
            "previous_processed_acquisition":
                previous,
            "candidate_count_checked":
                len(candidates),
            "candidates":
                candidates,
            "update_available":
                selected is not None,
            "selected_update":
                selected,
        }

        if selected is not None:
            result["updates_available"] = True

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()