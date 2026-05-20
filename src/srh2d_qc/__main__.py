from pathlib import Path
import sys
from srh2d_qc.qc_engine.runner import run_all_qc

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m srh2d_qc <model_dir>")
        raise SystemExit(1)

    model_dir = Path(sys.argv[1])
    results = run_all_qc(model_dir)

    # Temporary: just print a tiny summary
    print(f"Mesh elements: {len(results.mesh_quality)}")
    print(f"BCs: {len(results.bc_consistency)}")
    print(f"Missing materials: {results.material_coverage.missing_material_ids}")
    print(f"Timestep violations: {results.timestep_stability.num_violations}")

if __name__ == "__main__":
    main()
