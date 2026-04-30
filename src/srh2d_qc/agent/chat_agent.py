from __future__ import annotations
import json
from typing import Any, Dict, List

from openai import OpenAI
from srh2d_qc.agent.agent_core import SRH2D_QCAgent


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
            "get_qc_summary": self.qc_agent.tools.get_qc_summary,

            # WRAPPED agent-level tools
            "run_qc": self._tool_run_qc,
            "analyze_qc": self._tool_analyze_qc,
            "propose_actions": self._tool_propose_actions,
            "llm_analyze": self._tool_llm_analyze,
        }


        self.system_prompt = (
            "You are an SRH-2D modeling assistant. "
            "You MUST use the provided tools when needed. "
            "You MUST NOT invent tool names. "
            "If you need to count materials, call get_material_ids and count the list. "
            "Always produce a final natural-language answer after tool calls."
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
                    "name": "get_qc_summary",
                    "description": "Return a compact QC summary.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
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
