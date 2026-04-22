from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

from assignment_chat_2.prompts import return_system_prompt
from assignment_chat_2.tools_api import get_anime_details
from assignment_chat_2.tools_search import semantic_anime_search
from assignment_chat_2.tools_functions import query_anime_database
from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv(".env")
load_dotenv(".secrets")

_MAX_HISTORY_MESSAGES = 20  # sliding window for memory management

tools = [get_anime_details, semantic_anime_search, query_anime_database]

_GATEWAY_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"
_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.7,
    openai_api_key="any_value",
    openai_api_base=_GATEWAY_URL,
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY", "")},
)


def call_model(state: MessagesState):
    messages = state["messages"]
    # sliding window: keep system prompt + last N messages
    if len(messages) > _MAX_HISTORY_MESSAGES:
        messages = messages[-_MAX_HISTORY_MESSAGES:]

    response = _model.bind_tools(tools).invoke(
        [SystemMessage(content=return_system_prompt())] + messages
    )
    return {"messages": [response]}


def get_graph():
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder.compile()
