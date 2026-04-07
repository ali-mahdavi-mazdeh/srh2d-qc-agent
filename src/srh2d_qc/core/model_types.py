from dataclasses import dataclass
import numpy as np

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
