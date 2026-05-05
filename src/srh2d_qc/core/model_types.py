from dataclasses import dataclass
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class Mesh:
    nodes: np.ndarray          # shape (N, 2)
    node_ids: np.ndarray       # shape (N,) original SRH-2D node IDs
    elements: np.ndarray       # shape (M, 4)
    element_ids: np.ndarray    # shape (M,)
    material_ids: np.ndarray   # shape (M,)

    def get_element_nodes(self, eid):
        idx = np.where(self.element_ids == eid)[0][0]
        node_indices = self.elements[idx]
        node_ids = self.node_ids[node_indices]
        coords = self.nodes[node_indices]
        return node_ids, coords

@dataclass
class Material:
    id: int
    roughness: float
    name: Optional[str] = None   # human-readable label (from .srhmat or default)
    # type: Optional[str] = None   # optional category if you want it

@dataclass
class BoundaryCondition:
    name: str
    bc_type: str
    nodes: List[int] | None = None
    elements: List[int] | None = None
    timeseries: List[tuple[float, float]] | None = None

@dataclass
class RunConfig:
    dt: float
    total_time: float
    output_interval: float
    solver: str | None = None

# ---------------------------------------------------------
# Per-element mesh quality metrics
# ---------------------------------------------------------
@dataclass
class MeshQualityElement:
    element_id: int
    min_angle: float
    max_angle: float
    aspect_ratio: float
    skewness: float
    area: float


# ---------------------------------------------------------
# Global summary statistics for the entire mesh
# ---------------------------------------------------------
@dataclass
class MeshQualitySummary:
    min_angle: float
    max_angle: float
    min_aspect_ratio: float
    max_aspect_ratio: float
    min_skewness: float
    max_skewness: float
    min_area: float
    max_area: float


# ---------------------------------------------------------
# Container returned by compute_mesh_quality()
# ---------------------------------------------------------
@dataclass
class MeshQualityResult:
    per_element: List[MeshQualityElement]
    summary: MeshQualitySummary
@dataclass
class BCConsistencyResult:
    bc_name: str
    issues: List[str]
@dataclass
class MaterialCoverageResult:
    missing_material_ids: List[int]
    unused_material_ids: List[int]
    element_counts: Dict[int, int]

@dataclass
class TimestepStabilityResult:
    dt: float
    min_geom_dt: float
    median_geom_dt: float
    num_violations: int
    violation_element_ids: List[int]

@dataclass
class QCResults:
    mesh_quality: MeshQualityResult
    bc_consistency: List[BCConsistencyResult]
    material_coverage: MaterialCoverageResult
    timestep_stability: TimestepStabilityResult

@dataclass
class SRH2DModel:
    mesh: "Mesh"
    materials: Dict[int, "Material"]          # final merged materials
    material_assignments: Dict[int, int]      # elem_id → mat_id
    bcs: List["BoundaryCondition"]
    run_config: "RunConfig"
    model_dir: Path

    # # internal temporary stores (populated by parsers)
    # material_names: Optional[Dict[int, str]] = None     # from .srhmat
    # material_roughness: Optional[Dict[int, float]] = None  # from .srhydro