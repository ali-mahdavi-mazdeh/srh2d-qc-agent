from __future__ import annotations
import numpy as np
from srh2d_qc.core.model_types import Mesh, MeshQualityResult


def compute_mesh_quality(mesh: Mesh) -> list[MeshQualityResult]:
    """
    Compute basic mesh quality metrics for each element:
      - minimum internal angle (degrees)
      - maximum internal angle (degrees)
      - aspect ratio
      - skewness
      - area

    Supports triangles and quads.

    Parameters
    ----------
    mesh : Mesh
        Parsed mesh object.

    Returns
    -------
    list[MeshQualityResult]
        One entry per element.
    """

    results: list[MeshQualityResult] = []

    nodes = mesh.nodes
    elements = mesh.elements
    elem_ids = mesh.element_ids

    for eid, conn in zip(elem_ids, elements):
        # Remove padding (-1 for triangles)
        conn = conn[conn >= 0]
        pts = nodes[conn]

        # Compute edge lengths
        edges = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)

        # Compute internal angles
        angles = _compute_internal_angles(pts)

        # Aspect ratio = longest edge / shortest edge
        aspect_ratio = edges.max() / edges.min()

        # Skewness = max deviation from ideal angle
        ideal = 60.0 if len(conn) == 3 else 90.0
        skewness = np.max(np.abs(angles - ideal))

        # Area
        area = _polygon_area(pts)

        results.append(
            MeshQualityResult(
                element_id=int(eid),
                min_angle=float(angles.min()),
                max_angle=float(angles.max()),
                aspect_ratio=float(aspect_ratio),
                skewness=float(skewness),
                area=float(area),
            )
        )

    return results


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def _compute_internal_angles(pts: np.ndarray) -> np.ndarray:
    """Compute internal angles (degrees) for a polygon."""
    n = len(pts)
    angles = np.zeros(n)

    for i in range(n):
        p_prev = pts[i - 1]
        p_curr = pts[i]
        p_next = pts[(i + 1) % n]

        v1 = p_prev - p_curr
        v2 = p_next - p_curr

        # Normalize
        v1 /= np.linalg.norm(v1)
        v2 /= np.linalg.norm(v2)

        # Angle via dot product
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angles[i] = np.degrees(np.arccos(dot))

    return angles


def _polygon_area(pts: np.ndarray) -> float:
    """Compute polygon area using the shoelace formula."""
    x = pts[:, 0]
    y = pts[:, 1]
    return 0.5 * np.abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
