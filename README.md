# srh2d-qc-agent

A lightweight agentic AI tool for automated quality control of SRH‑2D hydraulic models.

how to run:

from srh2d_qc.qc_engine.runner import run_all_qc
from srh2d_qc.qc_engine.report import generate_markdown_report

results = run_all_qc("path/to/model")
report = generate_markdown_report(results)
print(report)
