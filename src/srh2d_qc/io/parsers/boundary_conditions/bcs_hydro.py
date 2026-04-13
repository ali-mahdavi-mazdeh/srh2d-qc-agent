from pathlib import Path
from typing import List
from srh2d_qc.core.model_types import BoundaryCondition


from pathlib import Path
from srh2d_qc.core.model_types import BoundaryCondition


from pathlib import Path
from srh2d_qc.core.model_types import BoundaryCondition


def parse_bcs_from_hydro(hydro_path: Path):
    """
    Parse SMS/XMS SRHHYDRO BC lines:
        BC <id> <type>
    """
    bcs = []

    with hydro_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            if parts[0].upper() == "BC":
                bc_name = parts[1]          # string
                bc_type = parts[2].upper()  # INLET-Q, EXIT-H, etc.

                bcs.append(
                    BoundaryCondition(
                        name=bc_name,
                        bc_type=bc_type,
                        nodes=None,
                        elements=None,
                        timeseries=None
                    )
                )

    return bcs
