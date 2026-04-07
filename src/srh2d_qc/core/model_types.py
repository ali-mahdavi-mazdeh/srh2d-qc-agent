from dataclasses import dataclass
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


@dataclass
class Mesh:
    nodes: np.ndarray          # (N, 2) float64
    elements: np.ndarray       # (M, 3 or 4) int64
    element_ids: np.ndarray    # (M,) int64
    material_ids: np.ndarray   # (M,) int64

@dataclass
class Material:
    id: int
    roughness: float
    type: str | None = None

@dataclass
class BoundaryCondition:
    name: str
    bc_type: str
    nodes: list[int] | None = None
    elements: list[int] | None = None
    timeseries: list[tuple[float, float]] | None = None

@dataclass
class RunConfig:
    dt: float
    total_time: float
    output_interval: float
    solver: str | None = None

@dataclass
class MeshQualityResult:
    element_id: int
    min_angle: float
    max_angle: float
    aspect_ratio: float
    skewness: float
    area: float

@dataclass
class BCConsistencyResult:
    bc_name: str
    issues: list[str]
@dataclass
class MaterialCoverageResult:
    missing_material_ids: list[int]
    unused_material_ids: list[int]
    element_counts: dict[int, int]

@dataclass
class TimestepStabilityResult:
    dt: float
    min_geom_dt: float
    median_geom_dt: float
    num_violations: int
    violation_element_ids: list[int]

@dataclass
class QCResults:
    mesh_quality: List[MeshQualityResult]
    bc_consistency: List[BCConsistencyResult]
    material_coverage: MaterialCoverageResult
    timestep_stability: TimestepStabilityResult

@dataclass
class SRH2DModel:
    mesh: "Mesh"
    materials: Dict[int, "Material"]
    bcs: List["BoundaryCondition"]
    run_config: "RunConfig"
    model_dir: Path