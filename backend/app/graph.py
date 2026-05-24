try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:  # compatibility with older langgraph versions
    from langgraph.checkpoint.memory import MemorySaver as InMemorySaver

from langgraph.graph import END, START, StateGraph

from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node
from app.nodes.supervisor import route_from_supervisor, supervisor_node
from app.state import MedicalState


builder = StateGraph(MedicalState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("diagnostic_agent", diagnostic_agent_node)
builder.add_node("physician_review", physician_review_node)
builder.add_node("report_agent", report_agent_node)

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "diagnostic_agent": "diagnostic_agent",
        "physician_review": "physician_review",
        "report_agent": "report_agent",
        "FINISH": END,
    },
)

builder.add_edge("diagnostic_agent", "supervisor")
builder.add_edge("physician_review", "supervisor")
builder.add_edge("report_agent", "supervisor")

graph = builder.compile()
api_graph = builder.compile(checkpointer=InMemorySaver())
