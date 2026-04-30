from dataclasses import asdict
from typing import Any, Dict, List

from srh2d_qc.core.model_types import SRH2DModel, QCResults


class ModelTools:
    """
    Thin, safe wrapper around an SRH2DModel + QCResults.
    All returned values are JSON-serializable.
    """

    def __init__(self, model: SRH2DModel, qc_results: QCResults | None = None):
        self.model = model
        self.qc_results = qc_results

    # -----------------------------
    # MODEL INSPECTION TOOLS
    # -----------------------------
    def get_element_count(self) -> int:
        return len(self.model.mesh.elements)

    def get_node_count(self) -> int:
        return len(self.model.mesh.nodes)

    def get_material_ids(self) -> List[int]:
        return sorted(self.model.materials.keys())

    def get_material_table(self) -> List[Dict[str, Any]]:
        """
        Returns a JSON-safe list of material info:
        [
          {"id": 1, "name": "Main channel", "roughness": 0.035},
          ...
        ]
        """
        rows = []
        for mid, mat in self.model.materials.items():
            rows.append(
                {
                    "id": mid,
                    "name": getattr(mat, "name", f"Material {mid}"),
                    "roughness": getattr(mat, "roughness", None),
                }
            )
        return rows

    def get_element_nodes(self, element_id: int) -> Dict[str, Any]:
        mesh = self.model.mesh

        # Find index of this element
        idx = int((mesh.element_ids == element_id).nonzero()[0][0])

        # Node indices → node IDs
        node_indices = mesh.elements[idx]
        node_ids = mesh.node_ids[node_indices]

        return {
            "element_id": element_id,
            "node_ids": [int(n) for n in node_ids]
        }

    def get_element_type(self, element_id: int) -> str:
        mesh = self.model.mesh

        idx = int((mesh.element_ids == element_id).nonzero()[0][0])
        node_indices = mesh.elements[idx]
        n = len(node_indices)

        if n == 3:
            return "triangle"
        elif n == 4:
            return "quadrilateral"
        else:
            return f"{n}-node polygon"


    # -----------------------------
    # QC TOOLS
    # -----------------------------
    def get_qc_summary(self) -> Dict[str, Any]:
        """
        Returns a compact, JSON-safe QC summary.
        """
        if not self.qc_results:
            return {"has_qc": False}

        mq = (
            asdict(self.qc_results.mesh_quality.summary)
            if self.qc_results.mesh_quality
            else None
        )

        ts = self.qc_results.timestep_stability
        mc = self.qc_results.material_coverage
        bc_list = self.qc_results.bc_consistency

        return {
            "has_qc": True,
            "mesh_quality": mq,
            "timestep_stability": {
                "dt": ts.dt,
                "min_geom_dt": ts.min_geom_dt,
                "median_geom_dt": ts.median_geom_dt,
                "num_violations": ts.num_violations,
            },
            "material_coverage": {
                "missing_material_ids": list(mc.missing_material_ids),
                "unused_material_ids": list(mc.unused_material_ids),
            },
            "bc_consistency": [
                {
                    "bc_name": bc.bc_name,
                    "issues": bc.issues,
                }
                for bc in bc_list
            ],
        }
