"""Explicit, reproducible study settings."""

from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class StudyConfig:
    study_name: str
    boundary_description: str
    bbox_wgs84: tuple[float, float, float, float]
    start_date: str
    end_date_exclusive: str
    collection_id: str = "LANDSAT/LC08/C02/T1_L2"
    analysis_crs: str = "EPSG:32643"
    grid_size_m: int = 100
    scene_cloud_cover_max_pct: float = 80
    max_lst_uncertainty_k: float = 2
    min_distance_from_cloud_km: float = 0.3
    min_valid_fraction_per_cell: float = 0.7
    min_scene_valid_area_fraction: float = 0.6
    max_scenes_to_audit: int = 60

    def __post_init__(self):
        west, south, east, north = self.bbox_wgs84
        if not all(math.isfinite(v) for v in self.bbox_wgs84):
            raise ValueError("Boundary coordinates must be finite.")
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("bbox_wgs84 must be [west, south, east, north].")
        if date.fromisoformat(self.start_date) >= date.fromisoformat(self.end_date_exclusive):
            raise ValueError("The start date must precede the exclusive end date.")
        if self.collection_id != "LANDSAT/LC08/C02/T1_L2":
            raise ValueError("Day 1 supports Landsat 8 Collection 2 Level-2 only.")
        if self.analysis_crs != "EPSG:32643":
            raise ValueError("This Bengaluru pilot uses WGS 84 / UTM zone 43N.")
        if self.grid_size_m != 100:
            raise ValueError("Day 1 uses an explicitly aligned 100 m grid.")
        for name in ("min_valid_fraction_per_cell", "min_scene_valid_area_fraction"):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 < value <= 1:
                raise ValueError(f"{name} must be greater than 0 and at most 1.")
        if not math.isfinite(self.scene_cloud_cover_max_pct) or not 0 <= self.scene_cloud_cover_max_pct <= 100:
            raise ValueError("Scene cloud cover must be between 0 and 100 percent.")
        if not math.isfinite(self.max_lst_uncertainty_k) or self.max_lst_uncertainty_k <= 0:
            raise ValueError("LST uncertainty limit must be positive and finite.")
        if not math.isfinite(self.min_distance_from_cloud_km) or self.min_distance_from_cloud_km < 0:
            raise ValueError("Cloud distance must be nonnegative and finite.")
        if not isinstance(self.max_scenes_to_audit, int) or not 1 <= self.max_scenes_to_audit <= 100:
            raise ValueError("Audit between 1 and 100 scenes per request.")

    @property
    def grid_transform(self):
        # One origin and orientation for every date and every exported layer.
        return [self.grid_size_m, 0, 0, 0, -self.grid_size_m, 0]

    def to_dict(self):
        return asdict(self)


def load_config(path: str | Path) -> StudyConfig:
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    values["bbox_wgs84"] = tuple(values["bbox_wgs84"])
    return StudyConfig(**values)
