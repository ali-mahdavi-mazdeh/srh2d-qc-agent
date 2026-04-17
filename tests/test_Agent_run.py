from srh2d_qc.agent.agent_core import SRH2D_QCAgent
from srh2d_qc.llm.reasoner import LLMReasoner

# Dummy LLM client for testing
def fake_llm(prompt: str) -> str:
    return """
    {
        "summary": "Test summary: QC issues detected.",
        "prioritized_actions": ["Assign default material", "Reduce dt"],
        "notes": "This is a test LLM response."
    }
    """

llm = LLMReasoner(llm_client=fake_llm)

def test_agent(model_dir):
    agent = SRH2D_QCAgent(model_dir, llm_reasoner=llm)

    agent.load()
    agent.run_qc()
    agent.analyze_qc()

    print("Detected issues:", agent.state.detected_issues)

    # Apply deterministic fixes
    agent.apply_fixes()

    # Re-run QC after fixes
    agent.run_qc()
    agent.analyze_qc()

    # Run LLM reasoning
    rec = agent.llm_analyze()

    print("\nLLM Summary:", rec.summary)
    print("LLM Prioritized Actions:", rec.prioritized_actions)
    print("LLM Notes:", rec.notes)
