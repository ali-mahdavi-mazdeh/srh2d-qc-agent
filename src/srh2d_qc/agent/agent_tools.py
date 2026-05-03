from dataclasses import asdict
from typing import Any, Dict, List
import logging
import csv
from pathlib import Path

from srh2d_qc.core.model_types import SRH2DModel, QCResults

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - plotting tools will not work")


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
    
    def get_all_model_class(
        self,
        include_mesh: bool = False,
        include_materials: bool = False,
        include_bcs: bool = False,
        include_run_config: bool = False,
    ) -> Dict[str, Any]:
        """
        Return selected model components. Default: all False (return empty).
        Set specific flags to include only needed sections.
        """
        # Log what was requested
        requested = {
            "mesh": include_mesh,
            "materials": include_materials,
            "bcs": include_bcs,
            "run_config": include_run_config,
        }
        logger.info(f"get_all_model_class requested: {requested}")
        
        result = {}
        
        if include_mesh:
            result["mesh"] = asdict(self.model.mesh)
        
        if include_materials:
            result["materials"] = {mid: asdict(mat) for mid, mat in self.model.materials.items()}
        
        if include_bcs:
            result["bcs"] = [asdict(bc) for bc in self.model.bcs]
        
        if include_run_config:
            result["run_config"] = asdict(self.model.run_config)
        
        return result

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

    def get_mesh_node_coordinates(self) -> Dict[str, Any]:
        """
        Return all mesh node coordinates in a plottable format.
        Returns: {"x_coords": [...], "y_coords": [...], "num_nodes": N}
        """
        mesh = self.model.mesh
        x_coords = [float(x) for x, y in mesh.nodes]
        y_coords = [float(y) for x, y in mesh.nodes]
        
        return {
            "x_coords": x_coords,
            "y_coords": y_coords,
            "num_nodes": len(x_coords),
        }


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

    # -----------------------------
    # EXPORT TOOLS
    # -----------------------------
    def export_mesh_nodes_csv(self, output_dir: str = ".") -> Dict[str, Any]:
        """
        Export all mesh nodes and their coordinates to a CSV file.
        Returns: {"status": "success", "file_path": "..."}
        """
        output_path = Path(output_dir) / "mesh_nodes.csv"
        
        try:
            mesh = self.model.mesh
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["node_id", "x", "y"])
                
                for i, node_id in enumerate(mesh.node_ids):
                    x, y = mesh.nodes[i]
                    writer.writerow([int(node_id), float(x), float(y)])
            
            logger.info(f"Exported mesh nodes to {output_path}")
            return {
                "status": "success",
                "file_path": str(output_path),
                "num_nodes": len(mesh.node_ids),
            }
        except Exception as e:
            logger.error(f"Failed to export mesh nodes: {e}")
            return {"status": "error", "message": str(e)}

    def export_materials_csv(self, output_dir: str = ".") -> Dict[str, Any]:
        """
        Export material properties to a CSV file.
        Returns: {"status": "success", "file_path": "..."}
        """
        output_path = Path(output_dir) / "materials.csv"
        
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["material_id", "name", "roughness"])
                
                for mid, mat in sorted(self.model.materials.items()):
                    name = getattr(mat, "name", f"Material {mid}")
                    roughness = getattr(mat, "roughness", "")
                    writer.writerow([int(mid), name, roughness])
            
            logger.info(f"Exported materials to {output_path}")
            return {
                "status": "success",
                "file_path": str(output_path),
                "num_materials": len(self.model.materials),
            }
        except Exception as e:
            logger.error(f"Failed to export materials: {e}")
            return {"status": "error", "message": str(e)}

    def save_csv(self, data: List[Dict[str, Any]], filename: str, output_dir: str = ".") -> Dict[str, Any]:
        """
        Generic CSV export tool. Accepts a list of dictionaries and saves as CSV.
        
        Args:
            data: List of dictionaries where each dict is a row
            filename: Name of the CSV file (e.g., "output.csv")
            output_dir: Output directory (default: current directory)
        
        Returns:
            {"status": "success", "file_path": "...", "num_rows": N}
        """
        output_path = Path(output_dir) / filename
        
        try:
            if not data:
                return {"status": "error", "message": "No data to save"}
            
            # Get headers from first row
            headers = list(data[0].keys())
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Saved CSV to {output_path} with {len(data)} rows")
            return {
                "status": "success",
                "file_path": str(output_path),
                "num_rows": len(data),
                "columns": headers,
            }
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            return {"status": "error", "message": str(e)}

    # -----------------------------
    # PLOTTING TOOLS
    # -----------------------------
    def plot_scatter(
        self,
        x_data: List[float],
        y_data: List[float],
        filename: str = "scatter.png",
        output_dir: str = ".",
        title: str = "Scatter Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
    ) -> Dict[str, Any]:
        """
        Create and save a scatter plot.
        
        Args:
            x_data: List of X values
            y_data: List of Y values
            filename: Name of the output PNG file
            output_dir: Output directory
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
        
        Returns:
            {"status": "success", "file_path": "..."}
        """
        if not MATPLOTLIB_AVAILABLE:
            return {"status": "error", "message": "matplotlib not installed"}
        
        output_path = Path(output_dir) / filename
        
        try:
            if len(x_data) != len(y_data):
                return {"status": "error", "message": "x_data and y_data must have same length"}
            print(f"Creating scatter plot with {len(x_data)} points")
            plt.figure(figsize=(10, 6))
            plt.scatter(x_data, y_data, alpha=0.6, edgecolors='k')
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved scatter plot to {output_path}")
            return {
                "status": "success",
                "file_path": str(output_path),
                "num_points": len(x_data),
            }
        except Exception as e:
            logger.error(f"Failed to create scatter plot: {e}")
            return {"status": "error", "message": str(e)}

    def plot_mesh(
        self,
        filename: str = "mesh.png",
        output_dir: str = ".",
        title: str = "Mesh Nodes",
    ) -> Dict[str, Any]:
        """
        Create and save a mesh plot directly (without returning coordinates to LLM).
        
        Args:
            filename: Name of the output PNG file
            output_dir: Output directory
            title: Plot title
        
        Returns:
            {"status": "success", "file_path": "...", "num_nodes": N}
        """
        if not MATPLOTLIB_AVAILABLE:
            return {"status": "error", "message": "matplotlib not installed"}
        
        output_path = Path(output_dir) / filename
        
        try:
            mesh = self.model.mesh
            x_coords = [float(x) for x, y in mesh.nodes]
            y_coords = [float(y) for x, y in mesh.nodes]
            
            plt.figure(figsize=(12, 8))
            plt.scatter(x_coords, y_coords, alpha=0.5, s=10, edgecolors='none')
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel("X Coordinates", fontsize=12)
            plt.ylabel("Y Coordinates", fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved mesh plot to {output_path} with {len(x_coords)} nodes")
            return {
                "status": "success",
                "file_path": str(output_path),
                "num_nodes": len(x_coords),
            }
        except Exception as e:
            logger.error(f"Failed to create mesh plot: {e}")
            return {"status": "error", "message": str(e)}
