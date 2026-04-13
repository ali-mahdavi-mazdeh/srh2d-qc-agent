from __future__ import annotations
from pathlib import Path
import numpy as np

from srh2d_qc.core.model_types import Mesh
from srh2d_qc.core.model_types import Material
from srh2d_qc.core.model_types import BoundaryCondition
from srh2d_qc.core.model_types import RunConfig

from pathlib import Path

def parse_run_config(path: Path):
    """
    Parse SMS/XMS SRHHYDRO format.

    Example:
        SimTime 0.0 1.0 15.0
        OutputInterval 1.0
        RunType FLOW
        UnsteadyOutput UNSTEADY
    """
    dt = None
    total_time = None
    output_interval = None
    run_type = None

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            tag = parts[0].upper()

            # SimTime t0 dt t_end
            if tag == "SIMTIME":
                # parts = ["SimTime", "0.0", "1.0", "15.0"]
                dt = float(parts[2])
                total_time = float(parts[3])

            elif tag == "OUTPUTINTERVAL":
                output_interval = float(parts[1])

            elif tag == "RUNTYPE":
                run_type = parts[1].upper()

    if dt is None or total_time is None:
        raise ValueError(
            f"Missing required run config fields in {path}: DT, TOTALTIME"
        )

    return {
        "dt": dt,
        "total_time": total_time,
        "output_interval": output_interval,
        "run_type": run_type,
    }
