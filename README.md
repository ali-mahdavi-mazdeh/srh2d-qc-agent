# SRH-2D QC Agent

Automated quality control for SRH-2D hydraulic models using agentic AI.

Built by [Ali Mahdavi Mazdeh, PhD](https://www.linkedin.com/in/ali-mahdavi-mazdeh) — water resources engineer specializing in computational hydraulics, HEC-RAS/SRH-2D automation, and AI-assisted modeling workflows.

---

## Demo

▶️ [Watch the SRH-2D QC Agent in action on YouTube](https://youtu.be/N4AZyzLmCgY?si=qcxfM4sMf_Yn5ITD)

---

## What It Does

Point the agent at an SRH-2D model folder and it automatically:

- **Parses mesh geometry** — reads `.srhgeom` files and checks cell quality metrics
- **Reviews boundary conditions** — validates inflow/outflow coverage and consistency from `.srhhydro` and `.bc` files
- **Validates material zones** — checks roughness assignments and flags unassigned mesh regions
- **Generates a structured QC report** — pass/fail results with flagged issues and recommendations
- **Answers natural language questions** — chat directly with your model using an AI agent interface

No more manual clicking through SMS. Run QC in seconds, get a report you can include in your deliverables.

---

## Requirements

To use the AI chat interface, you need an OpenAI API key.

1. Get your key at [platform.openai.com](https://platform.openai.com)
2. Copy `.env.example` to `.env` in the root folder
3. Add your key:

```
OPENAI_API_KEY=your-key-here
```

> **Note:** The QC checks (mesh, boundary conditions, materials) run without an API key. Only the AI chat interface requires one.

---

## Quick Start

```bash
pip install -e .
```

```python
from srh2d_qc.qc_engine.runner import run_all_qc
from srh2d_qc.qc_engine.report import generate_markdown_report

results = run_all_qc("path/to/your/srh2d/model")
report = generate_markdown_report(results)
print(report)
```
> **Note:** For chat agent: look /notebooks/testing_agent_chat_Demo.ipynb
---

## Project Structure

```
src/srh2d_qc/
├── io/
│   ├── model_loader.py
│   └── parsers/
│       ├── mesh.py
│       ├── materials.py
│       ├── run_config.py
│       └── boundary_conditions/
│           ├── bcs_hydro.py
│           ├── bcs_geom.py
│           ├── bcs_bcfile.py
│           └── bcs_unified.py
├── qc_engine/
│   ├── runner.py
│   └── report.py
└── agent/
    ├── agent_core.py
    ├── agent_loop.py
    └── agent_state.py
```

---

## Roadmap

- [x] Mesh geometry parsing and QC checks
- [x] Boundary condition review
- [x] Material/roughness zone validation
- [x] Natural language agent chat interface
- [ ] Output results validation (WSE, velocity, depth rasters)
- [ ] Mass balance and continuity error analysis
- [ ] Automated PDF/Word QC report generation
- [ ] MCP server for Claude Desktop integration
- [ ] QGIS plugin for in-map visualization

---

## Why This Exists

SRH-2D is widely used for 2D hydraulic modeling in FEMA flood studies, bridge scour analysis, and river engineering — but QC is still largely manual. This tool automates the tedious parts so engineers can focus on engineering judgment, not file parsing.

---

## Author

**Ali Mahdavi Mazdeh, PhD**
Water Resources Engineer | Computational Hydraulics | HEC-RAS · SRH-2D · HEC-HMS Automation | Python | AI/Agentic Workflows

- LinkedIn: [linkedin.com/in/ali-mahdavi-mazdeh](https://www.linkedin.com/in/ali-mahdavi-mazdeh)
- GitHub: [github.com/ali-mahdavi-mazdeh](https://github.com/ali-mahdavi-mazdeh)

---

## License

MIT License — free to use, modify, and distribute.
