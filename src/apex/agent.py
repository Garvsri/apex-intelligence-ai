
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from apex.ai_tools import (
    compare_f1_drivers,
    get_f1_season_leaderboard,
    get_f1_race_performance
)
from apex.rag import retrieve_context


# Local LLM
llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0,
)

# Analytics tools
tools = [
    compare_f1_drivers,
    get_f1_season_leaderboard,
    get_f1_race_performance,
]
llm_with_tools = llm.bind_tools(tools)


def assistant(state: MessagesState):
    question = state["messages"][-1].content

    # Retrieve relevant information from the F1 knowledge base.
    try:
        documents = retrieve_context(question, k=3)
        context = "\n\n".join(
            f"Source: {doc.metadata.get('source', 'unknown')}\n"
            f"{doc.page_content}"
            for doc in documents
        )
    except Exception:
        context = "F1 knowledge retrieval is currently unavailable."

    system_message = SystemMessage(
        content=(
            "You are Apex Intelligence AI, an F1 data analyst.\n"
            "Answer using retrieved F1 context when relevant.\n"
            "Use compare_f1_drivers for driver comparisons in the "
            "2024 British Grand Prix.\n"
            "Use get_f1_season_leaderboard for season-wide driver "
            "pace questions.\n"
            "Use get_f1_race_performance for questions about a specific "
            "Grand Prix. For best average race pace, report the "
            "best_mean_pace object directly. For fastest recorded lap, "
            "report the fastest_lap object. Never confuse these metrics.\n"
            "Supply the season year and full Grand Prix name.\n"
            "When asked for the best average race pace, select the driver "
            "with the LOWEST mean_lap_seconds in the tool output. Do not "
            "select the driver with the fastest_lap_seconds field for "
            "this question. The drivers list is sorted by mean lap time, "
            "lowest first.\n"
            "Treat mean_gap_seconds as driver A minus driver B: a "
            "negative value means driver A has the lower mean; a "
            "positive value means driver B has the lower mean.\n"
            "Race-normalized pace delta is descriptive, not a "
            "definitive measure of driver skill.\n"
            "Use official three-letter driver codes from tool output "
            "exactly. Never guess or substitute a driver's name.\n"
            "Use only these driver-code mappings when providing full names:\n"
            "VER = Max Verstappen; HAM = Lewis Hamilton; PER = Sergio Perez; "
            "BOT = Valtteri Bottas; RAI = Kimi Raikkonen; "
            "GIO = Antonio Giovinazzi; MSC = Mick Schumacher; "
            "MAZ = Nikita Mazepin; LEC = Charles Leclerc; "
            "SAI = Carlos Sainz; NOR = Lando Norris; "
            "RIC = Daniel Ricciardo; ALO = Fernando Alonso; "
            "OCO = Esteban Ocon; GAS = Pierre Gasly; "
            "TSU = Yuki Tsunoda; STR = Lance Stroll; "
            "VET = Sebastian Vettel; LAT = Nicholas Latifi; "
            "RUS = George Russell; ALB = Alexander Albon; "
            "DEV = Nyck de Vries; PIA = Oscar Piastri; "
            "ZHO = Zhou Guanyu; SAR = Logan Sargeant; "
            "HUL = Nico Hulkenberg; MAG = Kevin Magnussen; "
            "LAW = Liam Lawson; BEA = Oliver Bearman; "
            "COL = Franco Colapinto; ANT = Andrea Kimi Antonelli; "
            "DOO = Jack Doohan; DRU = Isack Hadjar; "
            "BOR = Gabriel Bortoleto; SHW = Robert Shwartzman.\n"
            "Never associate a driver code with a different driver name. "
            "SAI is Carlos Sainz; PER is Sergio Perez.\n"
            "Preserve exact driver codes and numerical values returned "
            "by tools. If a code is not listed, use the code alone.\n"
            "If neither retrieved context nor available tools answer "
            "the question, say so instead of inventing facts.\n\n"
            f"Retrieved F1 context:\n{context}"
        )
    )

    response = llm_with_tools.invoke(
        [system_message] + state["messages"]
    )

    return {"messages": [response]}


# Build the LangGraph workflow.
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile()


def ask_apex(question: str):
    result = graph.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"recursion_limit": 10},
    )
    return result["messages"][-1].content
