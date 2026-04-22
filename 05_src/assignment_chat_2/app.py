import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from assignment_chat_2.main import get_graph
from utils.logger import get_logger

_logs = get_logger(__name__)
load_dotenv(".secrets")

graph = get_graph()


def chat(message: str, history: list[dict]) -> str:
    _logs.info(f"User: {message}")

    langchain_messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))

    langchain_messages.append(HumanMessage(content=message))

    state = {"messages": langchain_messages}
    result = graph.invoke(state)

    reply = result["messages"][-1].content
    _logs.info(f"Assistant: {reply[:120]}...")
    return reply


chat_ui = gr.ChatInterface(
    fn=chat,
    type="messages",
    title="🎌 Otaku Oracle",
    description=(
        "Your all-knowing anime companion. Ask me about specific shows, "
        "describe the kind of anime you're in the mood for, or filter by genre, "
        "score, and type. I know my stuff — try me!"
    ),
    examples=[
        "Tell me about Neon Genesis Evangelion",
        "I want something sad and emotional, like a tearjerker",
        "Show me top-rated action TV anime with score above 9",
        "What's a good short movie about friendship?",
        "Find me horror anime that finished airing",
    ],
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    _logs.info("Starting Otaku Oracle...")
    chat_ui.launch()
