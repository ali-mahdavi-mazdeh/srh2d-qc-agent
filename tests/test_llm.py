from dotenv import load_dotenv
load_dotenv()

from srh2d_qc.llm.reasoner import LLMReasoner

# Minimal fake QC object for testing
class FakeQC:
    mesh_quality = type("obj", (), {"summary": "Mesh OK"})()
    material_coverage = "All materials assigned"
    timestep_stability = "dt too large"
    bc_consistency = []

qc = FakeQC()
proposed_actions = ["Reduce dt"]

llm = LLMReasoner()
result = llm.analyze_qc(qc, proposed_actions)

print("\n=== LLM RESULT ===")
print("Summary:", result["summary"])
print("Prioritized:", result["prioritized_actions"])
print("Notes:", result["notes"])
