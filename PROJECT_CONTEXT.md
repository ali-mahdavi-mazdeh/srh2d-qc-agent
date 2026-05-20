# Project Context for srh2d-qc-agent

## Project Overview
- **Name:** srh2d-qc-agent
- **Description:**
  - A Python-based quality control agent for SRH-2D hydrodynamic modeling projects.
  - Performs automated checks, reporting, and LLM-based reasoning on model input files and results.

## Directory Structure
- **activate_env.bat, install.bat, environment.yml**: Scripts and environment setup files.
- **pyproject.toml**: Python project configuration.
- **README.md**: Project documentation.
- **mesh_nodes.csv**: Example or reference mesh node data.
- **tests/**: Contains test scripts and sample model data.
- **src/srh2d_qc/**: Main package directory.
  - **agent/**: Core agent logic, state, tools, and chat interface.
  - **checks/**: Quality control checks (boundary conditions, materials, mesh quality, timestep stability).
  - **core/**: Utilities for boundary condition handling and model types.
  - **io/**: Model loading and parsing (materials, mesh, run config, boundary conditions).
  - **llm/**: LLM-based reasoning components.
  - **qc_engine/**: QC report generation and runner logic.
  - **utils/**: General utilities (e.g., material utilities).

## Key Files and Their Roles
- **src/srh2d_qc/agent/agent_core.py**: Main agent logic.
- **src/srh2d_qc/agent/agent_loop.py**: Agent execution loop.
- **src/srh2d_qc/agent/agent_state.py**: Agent state management.
- **src/srh2d_qc/agent/agent_tools.py**: Tools used by the agent.
- **src/srh2d_qc/agent/chat_agent.py**: Chat interface for agent.
- **src/srh2d_qc/agent/fix_strategies.py**: Automated fix strategies.
- **src/srh2d_qc/checks/**: Contains modules for various QC checks.
- **src/srh2d_qc/io/parsers/**: Parsers for materials, mesh, run config, and boundary conditions.
- **src/srh2d_qc/llm/reasoner.py**: LLM-based reasoning logic.
- **src/srh2d_qc/qc_engine/report.py**: Report generation.
- **src/srh2d_qc/qc_engine/runner.py**: QC engine runner.

## Notable Data Files
- **mesh_nodes.csv**: Example mesh node data.
- **tests/model_1, model_2, model_3/**: Sample model input files for testing.

## Environment
- **Python** (see environment.yml for dependencies)
- **.gitignore**: Ignores .env files.

## Usage
- Activate environment: `activate_env.bat`
- Install dependencies: `install.bat` or use `environment.yml`
- Run tests: See scripts in `tests/`
- Main entry point: `src/srh2d_qc/__main__.py`

## Additional Notes
- The project is modular, with clear separation between agent logic, QC checks, I/O, and LLM reasoning.
- Designed for extensibility and integration with LLMs for advanced reasoning and reporting.

---
This context file summarizes the structure and purpose of the srh2d-qc-agent project for use with LLMs or other tools requiring project context.
