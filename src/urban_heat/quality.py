"""Landsat Collection 2 constants and small, offline-checkable conversions.

Source: https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
These conversions apply to unscaled product values, not already scaled data.
"""

import math

LST_SCALE = 0.00341802
LST_OFFSET_K = 149.0
KELVIN_OFFSET = 273.15
REFLECTANCE_SCALE = 0.0000275
REFLECTANCE_OFFSET = -0.2
ST_UNCERTAINTY_SCALE = 0.01
CLOUD_DISTANCE_SCALE_KM = 0.01
# Fill, dilated cloud, cirrus, cloud, cloud shadow, snow. Water is retained.
REJECT_QA_PIXEL_BITS = 0b111111
NODATA = -9999.0


def landsat_dn_to_celsius(dn: float) -> float:
    """Convert a valid unscaled ST_B10 value; represent fill as NaN."""
    if not math.isfinite(dn) or not 0 < dn <= 65535:
        return math.nan
    return dn * LST_SCALE + LST_OFFSET_K - KELVIN_OFFSET


def qa_is_clear(qa_pixel: int, qa_radsat: int = 0) -> bool:
    """Conservative clear-pixel rule; excludes saturation and terrain occlusion."""
    if qa_pixel < 0 or qa_radsat < 0:
        return False
    return (qa_pixel & REJECT_QA_PIXEL_BITS) == 0 and qa_radsat == 0


def normalized_index(left: float, right: float) -> float:
    """Normalized difference of nonnegative, already scaled reflectances."""
    if not all(math.isfinite(v) and v >= 0 for v in (left, right)):
        return math.nan
    if left + right <= 1e-6:
        return math.nan
    return (left - right) / (left + right)
