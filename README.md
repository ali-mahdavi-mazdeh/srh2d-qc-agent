# srh2d-qc-agent

A lightweight agentic AI tool for automated quality control of SRH‑2D hydraulic models.

how to run:

from srh2d_qc.qc_engine.runner import run_all_qc
from srh2d_qc.qc_engine.report import generate_markdown_report

results = run_all_qc("path/to/model")
report = generate_markdown_report(results)
print(report)

io/
  model_loader.py

  parsers/
    mesh.py
      - parse_mesh
      - parse_srhgeom_mesh (YES, goes here)

    materials.py
      - parse_materials

    run_config.py
      - parse_run_config

    boundary_conditions/
      bcs_hydro.py
        - parse_bcs_from_hydro

      bcs_geom.py
        - parse_bcs_from_geom

      bcs_bcfile.py
        - parse_bcs_from_bcfile

      bcs_unified.py
        - parse_bcs_from_files   (main entry point)




src/
  srh2d_qc/
    __init__.py

    io/
      __init__.py
      model_loader.py

      parsers/
        __init__.py

        mesh.py
        materials.py
        run_config.py

        boundary_conditions/
          __init__.py
          bcs_hydro.py
          bcs_geom.py
          bcs_bcfile.py
          bcs_unified.py


srh2d_qc/
    agent/
        agent_state.py
        agent_core.py
        agent_loop.py
        fix_strategies.py