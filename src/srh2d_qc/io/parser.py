from __future__ import annotations
from pathlib import Path
import numpy as np

from srh2d_qc.core.model_types import Mesh
from srh2d_qc.core.model_types import Material
from srh2d_qc.core.model_types import BoundaryCondition
from srh2d_qc.core.model_types import RunConfig



def parse_mesh(mesh_path: Path) -> Mesh:
    """
    Parse an SRH‑2D / SMS .mesh file and return a Mesh object.

    Expected minimal format (QC‑oriented):
        ND   node_id   x   y
        E3T  elem_id   mat_id   n1   n2   n3
        E4Q  elem_id   mat_id   n1   n2   n3   n4

    Notes:
    - Lines beginning with '#', '!', or '//' are ignored.
    - Node and element IDs do not need to be ordered; they will be sorted.
    - Element connectivity is converted to 0‑based indexing.
    - Mixed element types (triangles + quads) are supported.
    - Only geometry and material IDs are parsed — no metadata.

    Parameters
    ----------
    mesh_path : Path
        Path to the .mesh file.

    Returns
    -------
    Mesh
        A Mesh dataclass containing:
            nodes: (N, 2) float64 array of coordinates
            elements: (M, K) int64 array of node indices (0‑based)
            element_ids: (M,) int64 array
            material_ids: (M,) int64 array

    Raises
    ------
    FileNotFoundError
        If the mesh file does not exist.
    ValueError
        If required sections are missing or malformed.
    """

    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh file not found: {mesh_path}")

    lines = mesh_path.read_text().splitlines()

    node_ids: list[int] = []
    node_coords: list[tuple[float, float]] = []

    elem_ids: list[int] = []
    elem_conn: list[list[int]] = []
    mat_ids: list[int] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue

        parts = line.split()
        tag = parts[0].upper()

        # -------------------------
        # Node line
        # -------------------------
        if tag == "ND":
            if len(parts) < 4:
                raise ValueError(f"Invalid ND line in {mesh_path}: {line}")
            nid = int(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            node_ids.append(nid)
            node_coords.append((x, y))
            continue

        # -------------------------
        # Element line
        # -------------------------
        if tag in ("E3T", "E4Q"):
            expected_min = 6 if tag == "E3T" else 7
            if len(parts) < expected_min:
                raise ValueError(f"Invalid {tag} line in {mesh_path}: {line}")

            eid = int(parts[1])
            mid = int(parts[2])
            conn = [int(n) for n in parts[3:]]

            elem_ids.append(eid)
            mat_ids.append(mid)
            elem_conn.append(conn)
            continue

        # Ignore other tags for now (e.g., headers)
        continue

    # -------------------------
    # Validate minimal content
    # -------------------------
    if not node_ids:
        raise ValueError(f"No ND (node) entries found in {mesh_path}")

    if not elem_ids:
        raise ValueError(f"No E3T/E4Q (element) entries found in {mesh_path}")

    # -------------------------
    # Convert to arrays
    # -------------------------
    node_ids = np.asarray(node_ids, dtype=np.int64)
    node_coords = np.asarray(node_coords, dtype=np.float64)

    elem_ids = np.asarray(elem_ids, dtype=np.int64)
    mat_ids = np.asarray(mat_ids, dtype=np.int64)

    # -------------------------
    # Sort nodes by ID
    # -------------------------
    node_sort_idx = np.argsort(node_ids)
    node_ids_sorted = node_ids[node_sort_idx]
    nodes_sorted = node_coords[node_sort_idx]

    # Map original node IDs → 0‑based indices
    id_to_idx = {nid: i for i, nid in enumerate(node_ids_sorted)}

    # -------------------------
    # Build element connectivity array
    # -------------------------
    max_nodes = max(len(c) for c in elem_conn)
    elements_arr = np.full((len(elem_conn), max_nodes), -1, dtype=np.int64)

    for i, conn in enumerate(elem_conn):
        elements_arr[i, :len(conn)] = [id_to_idx[n] for n in conn]

    # -------------------------
    # Sort elements by ID
    # -------------------------
    elem_sort_idx = np.argsort(elem_ids)
    elem_ids_sorted = elem_ids[elem_sort_idx]
    elements_sorted = elements_arr[elem_sort_idx]
    mat_ids_sorted = mat_ids[elem_sort_idx]

    # -------------------------
    # Return Mesh dataclass
    # -------------------------
    return Mesh(
        nodes=nodes_sorted,
        elements=elements_sorted,
        element_ids=elem_ids_sorted,
        material_ids=mat_ids_sorted,
    )



def parse_srhgeom_mesh(geom_path: Path) -> Mesh:
    """
    Parse the MESH block inside an SRH-2D .srhgeom file.

    Expected minimal structure:
        BEGIN MESH
          ND   node_id   x   y
          E3T  elem_id   mat_id   n1   n2   n3
          E4Q  elem_id   mat_id   n1   n2   n3   n4
        END MESH

    Only the MESH block is parsed here. Other blocks (MATERIAL, BC, etc.)
    are handled by separate parsers.

    Parameters
    ----------
    geom_path : Path
        Path to the .srhgeom file.

    Returns
    -------
    Mesh
        Mesh dataclass with nodes, elements, element_ids, material_ids.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the MESH block is missing or malformed.
    """

    if not geom_path.exists():
        raise FileNotFoundError(f".srhgeom file not found: {geom_path}")

    lines = geom_path.read_text().splitlines()

    in_mesh_block = False

    node_ids: list[int] = []
    node_coords: list[tuple[float, float]] = []

    elem_ids: list[int] = []
    elem_conn: list[list[int]] = []
    mat_ids: list[int] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue

        # Detect block boundaries
        if line.upper().startswith("BEGIN MESH"):
            in_mesh_block = True
            continue
        if line.upper().startswith("END MESH"):
            in_mesh_block = False
            continue

        if not in_mesh_block:
            continue

        # Inside MESH block
        parts = line.split()
        tag = parts[0].upper()

        # -------------------------
        # Node line
        # -------------------------
        if tag == "ND":
            if len(parts) < 4:
                raise ValueError(f"Invalid ND line in {geom_path}: {line}")
            nid = int(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            node_ids.append(nid)
            node_coords.append((x, y))
            continue

        # -------------------------
        # Element line
        # -------------------------
        if tag in ("E3T", "E4Q"):
            expected_min = 6 if tag == "E3T" else 7
            if len(parts) < expected_min:
                raise ValueError(f"Invalid {tag} line in {geom_path}: {line}")

            eid = int(parts[1])
            mid = int(parts[2])
            conn = [int(n) for n in parts[3:]]

            elem_ids.append(eid)
            mat_ids.append(mid)
            elem_conn.append(conn)
            continue

        # Ignore other tags inside MESH block
        continue

    # -------------------------
    # Validate minimal content
    # -------------------------
    if not node_ids:
        raise ValueError(f"No ND entries found in MESH block of {geom_path}")
    if not elem_ids:
        raise ValueError(f"No E3T/E4Q entries found in MESH block of {geom_path}")

    # -------------------------
    # Convert to arrays
    # -------------------------
    node_ids = np.asarray(node_ids, dtype=np.int64)
    node_coords = np.asarray(node_coords, dtype=np.float64)

    elem_ids = np.asarray(elem_ids, dtype=np.int64)
    mat_ids = np.asarray(mat_ids, dtype=np.int64)

    # -------------------------
    # Sort nodes by ID
    # -------------------------
    node_sort_idx = np.argsort(node_ids)
    node_ids_sorted = node_ids[node_sort_idx]
    nodes_sorted = node_coords[node_sort_idx]

    # Map original node IDs → 0-based indices
    id_to_idx = {nid: i for i, nid in enumerate(node_ids_sorted)}

    # -------------------------
    # Build element connectivity
    # -------------------------
    max_nodes = max(len(c) for c in elem_conn)
    elements_arr = np.full((len(elem_conn), max_nodes), -1, dtype=np.int64)

    for i, conn in enumerate(elem_conn):
        elements_arr[i, :len(conn)] = [id_to_idx[n] for n in conn]

    # -------------------------
    # Sort elements by ID
    # -------------------------
    elem_sort_idx = np.argsort(elem_ids)
    elem_ids_sorted = elem_ids[elem_sort_idx]
    elements_sorted = elements_arr[elem_sort_idx]
    mat_ids_sorted = mat_ids[elem_sort_idx]

    return Mesh(
        nodes=nodes_sorted,
        elements=elements_sorted,
        element_ids=elem_ids_sorted,
        material_ids=mat_ids_sorted,
    )




def parse_materials(path: Path) -> dict[int, Material]:
    """
    Parse SRH-2D material definitions from either:
      - a standalone .mat file, or
      - a MATERIAL block inside a .srhgeom file.

    Expected minimal format:
        MAT  mat_id  roughness

    Or inside .srhgeom:
        BEGIN MATERIAL
          MAT  mat_id  roughness
        END MATERIAL

    Parameters
    ----------
    path : Path
        Path to the .mat or .srhgeom file.

    Returns
    -------
    dict[int, Material]
        Dictionary keyed by material ID.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If no materials are found.
    """

    if not path.exists():
        raise FileNotFoundError(f"Material file not found: {path}")

    lines = path.read_text().splitlines()

    materials: dict[int, Material] = {}
    in_block = False
    is_geom = path.suffix.lower() == ".srhgeom"

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue

        # Detect MATERIAL block in .srhgeom
        if is_geom:
            if line.upper().startswith("BEGIN MATERIAL"):
                in_block = True
                continue
            if line.upper().startswith("END MATERIAL"):
                in_block = False
                continue
            if not in_block:
                continue

        # Parse MAT lines
        parts = line.split()
        tag = parts[0].upper()

        if tag == "MAT":
            if len(parts) < 3:
                raise ValueError(f"Invalid MAT line in {path}: {line}")

            mid = int(parts[1])
            roughness = float(parts[2])

            materials[mid] = Material(id=mid, roughness=roughness)
            continue

    if not materials:
        raise ValueError(f"No material definitions found in {path}")

    return materials



def parse_bcs(path: Path) -> list[BoundaryCondition]:
    """
    Parse SRH-2D boundary conditions from either:
      - a standalone .bc file, or
      - BOUNDARY blocks inside a .srhgeom file.

    Minimal supported structure:
        BEGIN BOUNDARY
          BC_NAME <name>
          BC_TYPE <type>
          BC_NODES n1 n2 n3 ...
          BC_ELEMS e1 e2 e3 ...
          BC_TS t value
        END BOUNDARY

    Parameters
    ----------
    path : Path
        Path to the .bc or .srhgeom file.

    Returns
    -------
    list[BoundaryCondition]
        List of parsed boundary conditions.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If no boundary conditions are found.
    """

    if not path.exists():
        raise FileNotFoundError(f"BC file not found: {path}")

    lines = path.read_text().splitlines()

    bcs: list[BoundaryCondition] = []
    in_block = False
    is_geom = path.suffix.lower() == ".srhgeom"

    # Temporary storage for one BC
    name = None
    bc_type = None
    nodes = []
    elems = []
    ts = []

    def finalize_bc():
        """Helper to finalize and store a BC."""
        if name and bc_type:
            bcs.append(
                BoundaryCondition(
                    name=name,
                    bc_type=bc_type,
                    nodes=nodes if nodes else None,
                    elements=elems if elems else None,
                    timeseries=ts if ts else None,
                )
            )

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue

        # Detect BOUNDARY block in .srhgeom
        if is_geom:
            if line.upper().startswith("BEGIN BOUNDARY"):
                in_block = True
                name = None
                bc_type = None
                nodes = []
                elems = []
                ts = []
                continue
            if line.upper().startswith("END BOUNDARY"):
                in_block = False
                finalize_bc()
                continue
            if not in_block:
                continue

        # Standalone .bc file
        if not is_geom:
            if line.upper().startswith("BEGIN BOUNDARY"):
                in_block = True
                name = None
                bc_type = None
                nodes = []
                elems = []
                ts = []
                continue
            if line.upper().startswith("END BOUNDARY"):
                in_block = False
                finalize_bc()
                continue
            if not in_block:
                continue

        # Inside a BOUNDARY block
        parts = line.split()
        tag = parts[0].upper()

        if tag == "BC_NAME":
            name = parts[1]
            continue

        if tag == "BC_TYPE":
            bc_type = parts[1].upper()
            continue

        if tag == "BC_NODES":
            nodes.extend(int(n) for n in parts[1:])
            continue

        if tag == "BC_ELEMS":
            elems.extend(int(e) for e in parts[1:])
            continue

        if tag == "BC_TS":
            if len(parts) < 3:
                raise ValueError(f"Invalid BC_TS line in {path}: {line}")
            t = float(parts[1])
            val = float(parts[2])
            ts.append((t, val))
            continue

        # Ignore other tags for now
        continue

    if not bcs:
        raise ValueError(f"No boundary conditions found in {path}")

    return bcs



def parse_run_config(path: Path) -> RunConfig:
    """
    Parse SRH-2D run configuration from a .srhhydro file.

    Minimal supported keywords (QC-oriented):
        DT <value>
        TOTALTIME <value>
        OUTPUTINTERVAL <value>
        SOLVER <string>        (optional)

    Parameters
    ----------
    path : Path
        Path to the .srhhydro file.

    Returns
    -------
    RunConfig
        Parsed run configuration.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If required fields are missing.
    """

    if not path.exists():
        raise FileNotFoundError(f"Run config file not found: {path}")

    lines = path.read_text().splitlines()

    dt = None
    total_time = None
    output_interval = None
    solver = None

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue

        parts = line.split()
        tag = parts[0].upper()

        if tag == "DT":
            if len(parts) < 2:
                raise ValueError(f"Invalid DT line in {path}: {line}")
            dt = float(parts[1])
            continue

        if tag == "TOTALTIME":
            if len(parts) < 2:
                raise ValueError(f"Invalid TOTALTIME line in {path}: {line}")
            total_time = float(parts[1])
            continue

        if tag == "OUTPUTINTERVAL":
            if len(parts) < 2:
                raise ValueError(f"Invalid OUTPUTINTERVAL line in {path}: {line}")
            output_interval = float(parts[1])
            continue

        if tag == "SOLVER":
            if len(parts) < 2:
                raise ValueError(f"Invalid SOLVER line in {path}: {line}")
            solver = parts[1]
            continue

        # Ignore other keywords for now
        continue

    # Validate required fields
    missing = []
    if dt is None:
        missing.append("DT")
    if total_time is None:
        missing.append("TOTALTIME")
    if output_interval is None:
        missing.append("OUTPUTINTERVAL")

    if missing:
        raise ValueError(
            f"Missing required run config fields in {path}: {', '.join(missing)}"
        )

    return RunConfig(
        dt=dt,
        total_time=total_time,
        output_interval=output_interval,
        solver=solver,
    )
