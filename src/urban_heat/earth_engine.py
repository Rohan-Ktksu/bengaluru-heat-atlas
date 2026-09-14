"""Day 1 Earth Engine pipeline; all remote calls require user authentication.

Returns satellite-derived surface temperatures, not air temperature or UTCI.
The map has a shared 100 m grid. Fine input pixels are aggregated with means;
they are not treated as independent 30 m thermal observations.
"""

import ee

from .config import StudyConfig
from .quality import (
    CLOUD_DISTANCE_SCALE_KM, KELVIN_OFFSET, LST_OFFSET_K, LST_SCALE,
    NODATA, REFLECTANCE_OFFSET, REFLECTANCE_SCALE, REJECT_QA_PIXEL_BITS,
    ST_UNCERTAINTY_SCALE,
)


def study_geometry(config: StudyConfig):
    return ee.Geometry.Rectangle(list(config.bbox_wgs84), proj="EPSG:4326", geodesic=False)


def _on_grid(image, config):
    return image.reduceResolution(
        reducer=ee.Reducer.mean(), maxPixels=1024
    ).reproject(crs=config.analysis_crs, crsTransform=config.grid_transform)


def _index(left, right, name):
    denominator = left.add(right)
    valid = left.gte(0).And(right.gte(0)).And(denominator.gt(1e-6))
    return left.subtract(right).divide(denominator).updateMask(valid).rename(name)


def prepare_landsat(image, config: StudyConfig):
    image = ee.Image(image)
    clear = image.select("QA_PIXEL").bitwiseAnd(REJECT_QA_PIXEL_BITS).eq(0)
    clear = clear.And(image.select("QA_RADSAT").eq(0))
    thermal_valid = clear.And(image.select("ST_B10").gt(0))
    thermal_valid = thermal_valid.And(
        image.select("ST_QA").multiply(ST_UNCERTAINTY_SCALE).lte(config.max_lst_uncertainty_k)
    ).And(
        image.select("ST_CDIST").multiply(CLOUD_DISTANCE_SCALE_KM).gte(config.min_distance_from_cloud_km)
    )
    lst = (
        image.select("ST_B10").multiply(LST_SCALE).add(LST_OFFSET_K)
        .subtract(KELVIN_OFFSET).updateMask(thermal_valid).rename("lst_c")
    )
    optical = (
        image.select(["SR_B4", "SR_B5", "SR_B6"])
        .multiply(REFLECTANCE_SCALE).add(REFLECTANCE_OFFSET).updateMask(thermal_valid)
    )
    ndvi = _index(optical.select("SR_B5"), optical.select("SR_B4"), "ndvi")
    ndbi = _index(optical.select("SR_B6"), optical.select("SR_B5"), "ndbi")

    # Unmask to zero BEFORE aggregation, so missing/cloudy pixels count toward
    # the denominator. Expanding the footprint also counts scene edges as missing.
    support = _on_grid(lst.mask().unmask(0, sameFootprint=False), config).rename("valid_fraction")
    averaged = _on_grid(lst.addBands(ndvi).addBands(ndbi), config)
    averaged = averaged.updateMask(support.gte(config.min_valid_fraction_per_cell))
    result = averaged.addBands(support).clip(study_geometry(config))
    observed = ee.Date(image.get("system:time_start"))
    return result.copyProperties(image, ["system:time_start", "LANDSAT_PRODUCT_ID", "CLOUD_COVER"]).set({
        "source_asset": ee.String(config.collection_id + "/").cat(ee.String(image.get("system:index"))),
        "observed_at_utc": observed.format("yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC"),
        "observed_at_ist": observed.format("yyyy-MM-dd HH:mm:ss", "Asia/Kolkata"),
        "product_type": "satellite_observation",
    })


def landsat_collection(config: StudyConfig):
    return (
        ee.ImageCollection(config.collection_id)
        .filterBounds(study_geometry(config))
        .filterDate(config.start_date, config.end_date_exclusive)
        .filter(ee.Filter.eq("PROCESSING_LEVEL", "L2SP"))
        .filter(ee.Filter.gte("CLOUD_COVER", 0))
        .filter(ee.Filter.lte("CLOUD_COVER", config.scene_cloud_cover_max_pct))
        .map(lambda image: prepare_landsat(image, config))
        .sort("system:time_start")
    )


def scene_inventory(collection, config: StudyConfig):
    """Return per-scene coverage and LST summaries; does not select dates silently."""
    count = collection.size().getInfo()
    if count == 0:
        raise ValueError("No candidate L2SP scenes. Review the date window and scene-cloud filter.")
    if count > config.max_scenes_to_audit:
        raise ValueError(
            f"Found {count} scenes; audit limit is {config.max_scenes_to_audit}. "
            "Use a shorter date window. No scenes have been silently dropped."
        )
    reduction = dict(
        geometry=study_geometry(config), crs=config.analysis_crs,
        crsTransform=config.grid_transform, maxPixels=10_000_000, tileScale=4,
    )
    area = ee.Image.pixelArea().rename("area")
    total_area = ee.Number(area.reduceRegion(reducer=ee.Reducer.sum(), **reduction).get("area"))

    def summarize(item):
        image = ee.Image(item)
        valid = image.select("lst_c").mask().unmask(0, sameFootprint=False)
        valid_area = ee.Number(area.multiply(valid).reduceRegion(
            reducer=ee.Reducer.sum(), **reduction
        ).get("area"))
        stats = image.select("lst_c").reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.percentile([5, 50, 95]), sharedInputs=True
            ), **reduction
        )
        fraction = valid_area.divide(total_area)
        return ee.Feature(None, stats).set({
            "source_asset": image.get("source_asset"),
            "landsat_product_id": image.get("LANDSAT_PRODUCT_ID"),
            "observed_at_utc": image.get("observed_at_utc"),
            "observed_at_ist": image.get("observed_at_ist"),
            "whole_scene_cloud_pct": image.get("CLOUD_COVER"),
            "valid_pilot_area_fraction": fraction,
            "eligible_for_preview": fraction.gte(config.min_scene_valid_area_fraction),
        })

    response = ee.FeatureCollection(collection.toList(count).map(summarize)).getInfo()
    return [feature["properties"] for feature in response["features"]]


def drive_export_task(image, config: StudyConfig, description: str):
    """Build an export task. Caller explicitly starts it in the notebook."""
    return ee.batch.Export.image.toDrive(
        image=image.select(["lst_c", "ndvi", "ndbi", "valid_fraction"])
        .toFloat().unmask(NODATA, sameFootprint=False).clip(study_geometry(config)),
        description=description, folder="BengaluruUrbanHeat", fileNamePrefix=description,
        region=study_geometry(config), crs=config.analysis_crs,
        crsTransform=config.grid_transform, maxPixels=100_000_000,
        fileFormat="GeoTIFF", formatOptions={"cloudOptimized": True, "noData": NODATA},
    )
