from __future__ import annotations
import json
from typing import Any, Dict, List
import logging

from openai import OpenAI
from srh2d_qc.agent.agent_core import SRH2D_QCAgent

logger = logging.getLogger(__name__)


class SRH2DChatAgent:
    """
    Conversational agent using OpenAI's official tool-calling API.
    Supports multi-step tool calls and final natural-language answers.
    """

    def __init__(self, qc_agent: SRH2D_QCAgent, model="gpt-4o-mini"):
        self.qc_agent = qc_agent
        self.model = model
        self.client = OpenAI()

        # Build tool schema for OpenAI
        self.tools = self._build_tool_schema()

        # Map tool names → Python functions
        self.tool_functions = {
            "get_element_count": self.qc_agent.tools.get_element_count,
            "get_node_count": self.qc_agent.tools.get_node_count,
            "get_material_ids": self.qc_agent.tools.get_material_ids,
            "get_material_table": self.qc_agent.tools.get_material_table,
            "get_element_nodes": self.qc_agent.tools.get_element_nodes,
            "get_element_type": self.qc_agent.tools.get_element_type,
            "get_mesh_node_coordinates": self.qc_agent.tools.get_mesh_node_coordinates,
            "get_node_coordinates": self.qc_agent.tools.get_node_coordinates,
            "get_qc_summary": self.qc_agent.tools.get_qc_summary,
            "get_all_model_class": self.qc_agent.tools.get_all_model_class,

            # Export tools
            "export_mesh_nodes_csv": self._tool_export_mesh_nodes,
            "export_materials_csv": self._tool_export_materials,
            "export_boundary_conditions_csv": self._tool_export_boundary_conditions,
            "save_csv": self._tool_save_csv,
            "plot_scatter": self._tool_plot_scatter,
            "plot_mesh": self._tool_plot_mesh,

            # WRAPPED agent-level tools
            "run_qc": self._tool_run_qc,
            "analyze_qc": self._tool_analyze_qc,
            "propose_actions": self._tool_propose_actions,
            "llm_analyze": self._tool_llm_analyze,
        }


        self.system_prompt = (
            "You are an SRH-2D modeling assistant. Use tools when needed. Do not invent tool names.\n"
            "Model has: mesh (nodes/elements), materials, boundary conditions (BCs), run config.\n"
            "IMPORTANT - Token Usage:\n"
            "  - get_all_model_class() fetches massive data and significantly increases token usage. Use ONLY if absolutely necessary.\n"
            "  - Prefer specific tools: get_material_ids(), get_material_table(), get_node_count(), etc.\n"
            "For mesh plotting: Use plot_mesh() directly (handles all nodes internally, no token overhead).\n"
            "For custom scatter plots: get data, then use plot_scatter().\n"
            "For data export: use save_csv() or export_*_csv() tools.\n"
            "Always answer in natural language after using tools."
        )

    # ---------------------------------------------------------
    # Tool schema for OpenAI
    # ---------------------------------------------------------
    def _tool_run_qc(self):
        # run_qc updates self.qc_agent.qc_results
        self.qc_agent.run_qc()
        # always return JSON-safe summary
        return self.qc_agent.tools.get_qc_summary()


    def _tool_analyze_qc(self):
        issues = self.qc_agent.analyze_qc()
        # if it's already a list of strings, just return it
        return issues


    def _tool_propose_actions(self):
        actions = self.qc_agent.propose_actions()
        # if it's a list of strings, return as-is; if it's objects, stringify
        if not actions:
            return []
        if isinstance(actions[0], str):
            return actions
        return [str(a) for a in actions]


    def _tool_llm_analyze(self):
        result = self.qc_agent.llm_analyze()
        # if it's already a string or dict, return as-is
        if isinstance(result, (str, dict, list, int, float, bool)) or result is None:
            return result
        # fallback: stringify
        return str(result)

    def _tool_export_mesh_nodes(self, output_dir: str = ".") -> Dict[str, Any]:
        result = self.qc_agent.tools.export_mesh_nodes_csv(output_dir)
        return result

    def _tool_export_materials(self, output_dir: str = ".") -> Dict[str, Any]:
        result = self.qc_agent.tools.export_materials_csv(output_dir)
        return result

    def _tool_export_boundary_conditions(self, output_dir: str = ".") -> Dict[str, Any]:
        result = self.qc_agent.tools.export_boundary_conditions_csv(output_dir)
        return result

    def _tool_save_csv(self, data: List[Dict[str, Any]], filename: str, output_dir: str = ".") -> Dict[str, Any]:
        result = self.qc_agent.tools.save_csv(data, filename, output_dir)
        return result

    def _tool_plot_scatter(
        self,
        x_data: List[float],
        y_data: List[float],
        filename: str = "scatter.png",
        output_dir: str = ".",
        title: str = "Scatter Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
    ) -> Dict[str, Any]:
        result = self.qc_agent.tools.plot_scatter(x_data, y_data, filename, output_dir, title, xlabel, ylabel)
        return result

    def _tool_plot_mesh(
        self,
        filename: str = "mesh.png",
        output_dir: str = ".",
        title: str = "Mesh Nodes",
    ) -> Dict[str, Any]:
        result = self.qc_agent.tools.plot_mesh(filename, output_dir, title)
        return result

    def _build_tool_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_element_count",
                    "description": "Return the number of mesh elements.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_node_count",
                    "description": "Return the number of mesh nodes.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_material_ids",
                    "description": "Return the list of material IDs.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_material_table",
                    "description": "Return material properties as a list of dicts.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_element_nodes",
                    "description": "Return node IDs for a given element.",
                    "parameters": {
                        "type": "object",
                        "properties": {"element_id": {"type": "integer"}},
                        "required": ["element_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_element_type",
                    "description": "Return the element type (triangle, quadrilateral, etc).",
                    "parameters": {
                        "type": "object",
                        "properties": {"element_id": {"type": "integer"}},
                        "required": ["element_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_mesh_node_coordinates",
                    "description": "Return all mesh node coordinates as separate X and Y lists, ready for plotting.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_node_coordinates",
                    "description": "Return coordinates for specific nodes. Pass a list of node IDs to get their X and Y coordinates for plotting.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node_ids": {
                                "type": "array",
                                "description": "List of node IDs to retrieve coordinates for",
                                "items": {"type": "integer"},
                            },
                        },
                        "required": ["node_ids"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_qc_summary",
                    "description": "Return a compact QC summary.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_model_class",
                    "description": "Return selected model components (mesh, materials, BCs, run_config). Specify which sections you need to minimize data transfer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_mesh": {
                                "type": "boolean",
                                "description": "Include mesh data (nodes, elements, IDs)",
                                "default": False,
                            },
                            "include_materials": {
                                "type": "boolean",
                                "description": "Include material definitions",
                                "default": False,
                            },
                            "include_bcs": {
                                "type": "boolean",
                                "description": "Include boundary conditions",
                                "default": False,
                            },
                            "include_run_config": {
                                "type": "boolean",
                                "description": "Include simulation run configuration",
                                "default": False,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "export_mesh_nodes_csv",
                    "description": "Export all mesh nodes and coordinates to a CSV file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for the CSV file (default: current directory)",
                                "default": ".",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "export_materials_csv",
                    "description": "Export material properties to a CSV file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for the CSV file (default: current directory)",
                                "default": ".",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "export_boundary_conditions_csv",
                    "description": "Export boundary conditions to a CSV file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for the CSV file (default: current directory)",
                                "default": ".",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_csv",
                    "description": "Generic tool to save any data as a CSV file. Pass a list of dictionaries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "description": "List of dictionaries (rows). Each dict should have the same keys.",
                                "items": {"type": "object"},
                            },
                            "filename": {
                                "type": "string",
                                "description": "Name of the CSV file to create (e.g., 'output.csv')",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory (default: current directory)",
                                "default": ".",
                            },
                        },
                        "required": ["data", "filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "plot_scatter",
                    "description": "Create and save a scatter plot as PNG.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x_data": {
                                "type": "array",
                                "description": "List of X values (numbers)",
                                "items": {"type": "number"},
                            },
                            "y_data": {
                                "type": "array",
                                "description": "List of Y values (numbers)",
                                "items": {"type": "number"},
                            },
                            "filename": {
                                "type": "string",
                                "description": "Name of the output PNG file",
                                "default": "scatter.png",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory (default: current directory)",
                                "default": ".",
                            },
                            "title": {
                                "type": "string",
                                "description": "Plot title",
                                "default": "Scatter Plot",
                            },
                            "xlabel": {
                                "type": "string",
                                "description": "X-axis label",
                                "default": "X",
                            },
                            "ylabel": {
                                "type": "string",
                                "description": "Y-axis label",
                                "default": "Y",
                            },
                        },
                        "required": ["x_data", "y_data"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "plot_mesh",
                    "description": "Create and save a mesh plot (all nodes plotted directly). No need to fetch coordinates first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the output PNG file",
                                "default": "mesh.png",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory (default: current directory)",
                                "default": ".",
                            },
                            "title": {
                                "type": "string",
                                "description": "Plot title",
                                "default": "Mesh Nodes",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_qc",
                    "description": "Run all QC checks.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_qc",
                    "description": "Analyze QC results and return issue summaries.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "propose_actions",
                    "description": "Propose high-level actions based on QC results.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "llm_analyze",
                    "description": "Run LLM reasoning on QC results.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    # ---------------------------------------------------------
    # Main ask() method with multi-step tool calling
    # ---------------------------------------------------------
    def ask(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            # Assistant wants to call a tool
            if msg.tool_calls:
                # Append assistant message ONCE
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                })

                # For each tool call
                for tool_call in msg.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    # LOG: Show what tool is being called with what args
                    logger.info(f"Tool call: {name}({json.dumps(args)})")

                    result = self.tool_functions[name](**args)

                    # Append tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    })

                continue

            # No tool calls → final answer
            return msg.content

    # ---------------------------------------------------------
    # Interactive chat loop
    # ---------------------------------------------------------
    def chat(self):
        print("SRH-2D Chat Agent. Type 'exit' to quit.\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye.")
                break

            answer = self.ask(user_input)
            print(f"Agent: {answer}\n")
