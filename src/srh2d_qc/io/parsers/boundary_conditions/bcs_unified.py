from pathlib import Path
from typing import List

from srh2d_qc.core.model_types import BoundaryCondition
from .bcs_hydro import parse_bcs_from_hydro
from .bcs_geom import parse_bcs_from_geom
from .bcs_bcfile import parse_bcs_from_bcfile
from .bcs_geom import parse_nodestrings_from_geom

def parse_bcs_from_files(
    geom_path: Path,
    hydro_path: Path,
    model_dir: Path,
) -> List[BoundaryCondition]:
    """
    Unified BC parser that merges:
      1. BC types from .srhhydro
      2. BC node strings from .srhgeom
      3. Optional *.bc files
    """

    # ---------------------------------------------------------
    # 1. BC types from .srhhydro (INLET-Q, EXIT-H, etc.)
    # ---------------------------------------------------------
    bcs = parse_bcs_from_hydro(hydro_path)

    # Convert to dict for merging
    bc_dict = {bc.name: bc for bc in bcs}

    # ---------------------------------------------------------
    # 2. NodeStrings from .srhgeom (BC geometry)
    # ---------------------------------------------------------
    nodestrings = parse_nodestrings_from_geom(geom_path)

    for ns_id, node_list in nodestrings.items():
        if ns_id in bc_dict:
            bc_dict[ns_id].nodes = node_list
        else:
            # NodeString exists but no BC type in hydro → create BC
            bc_dict[ns_id] = BoundaryCondition(
                name=ns_id,
                bc_type="UNKNOWN",
                nodes=node_list,
                elements=None,
                timeseries=None
            )

    # ---------------------------------------------------------
    # 3. Optional *.bc files (rare)
    # ---------------------------------------------------------
    bc_files = list(model_dir.glob("*.bc"))
    for bc_file in bc_files:
        for bc in parse_bcs_from_bcfile(bc_file):
            if bc.name not in bc_dict:
                bc_dict[bc.name] = bc

    # ---------------------------------------------------------
    # 4. Return merged BC list
    # ---------------------------------------------------------
    return list(bc_dict.values())


# def parse_bcs_from_files(
#     geom_path: Path,
#     hydro_path: Path,
#     model_dir: Path,
# ) -> List[BoundaryCondition]:
#     """
#     Unified BC parser that supports:
#       1. Native SRH-2D BCs inside .srhhydro
#       2. SMS BCs inside .srhgeom
#       3. SMS/pyHMT2D BCs in separate .bc files

#     Priority order:
#       (1) .srhhydro
#       (2) .srhgeom
#       (3) *.bc files
#     """

#     # ---------------------------------------------------------
#     # 1. Native SRH-2D: BCs inside .srhhydro
#     # ---------------------------------------------------------
#     bcs = parse_bcs_from_hydro(hydro_path)
#     if bcs:
#         return bcs

#     # ---------------------------------------------------------
#     # 2. SMS fallback: BCs inside .srhgeom
#     # ---------------------------------------------------------
#     bcs = parse_bcs_from_geom(geom_path)
#     if bcs:
#         return bcs

#     # ---------------------------------------------------------
#     # 3. Legacy fallback: *.bc files (SMS / pyHMT2D)
#     # ---------------------------------------------------------
#     bc_files = list(model_dir.glob("*.bc"))
#     if bc_files:
#         all_bcs = []
#         for bc_file in bc_files:
#             all_bcs.extend(parse_bcs_from_bcfile(bc_file))
#         return all_bcs

#     # ---------------------------------------------------------
#     # 4. No BCs found (valid for some models)
#     # ---------------------------------------------------------
#     return []
