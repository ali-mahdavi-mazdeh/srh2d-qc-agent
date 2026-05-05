from dotenv import load_dotenv
load_dotenv()

from srh2d_qc.agent.agent_core import SRH2D_QCAgent
from srh2d_qc.llm.reasoner import LLMReasoner
from srh2d_qc.qc_engine.report import generate_markdown_report  # Assuming this is a function to generate a report from the agent's state

def test_full_agent(model_dir):
    model_dir = model_dir   # adjust if needed

    agent = SRH2D_QCAgent(model_dir, llm_reasoner=LLMReasoner())

    print("\n=== LOADING MODEL ===")
    agent.load()

    print("\n=== RUNNING QC ===")
    results = agent.run_qc()
    agent.analyze_qc()
    print("Detected issues:", agent.state.detected_issues)

    print("\n=== APPLYING FIXES ===")
    agent.apply_fixes()

    print("\n=== RE-RUNNING QC ===")
    agent.run_qc()
    agent.analyze_qc()
    print("Issues after fixes:", agent.state.detected_issues)

    print("\n=== RUNNING LLM REASONING ===")
    agent.llm_analyze()

    print("\n=== LLM OUTPUT ===")
    print("Summary:", agent.state.llm_summary)
    print("Prioritized:", agent.state.llm_prioritized_actions)
    print("Notes:", agent.state.llm_notes)

    print("\n=== AGENT HISTORY ===")
    for h in agent.state.history:
        print("-", h)
    return generate_markdown_report(results=results, state=agent.state)