from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated
from langchain_core.messages import AIMessage
import sqlite3
from nodes import starting_point, Nodes, Edges, NODE_MAP, generate_router_function

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    current_node: int | None
    user_info: dict | None
    user_name: str | None

def process_user_input(state: State) -> State:
    return state

def router(state: State):
    current_node = state["current_node"] if "current_node" in state else 0
    getNext = generate_router_function(Nodes, Edges)
    if current_node == 2 and "user_name" not in state:
        return getNext(current_node, get_current=True)
    next_node = getNext(current_node)
    return next_node

def build_graph():
    builder = StateGraph(State)
    
    for node in Nodes:
        curr_node = node["type"] + "-" + node["id"]
        node_func = NODE_MAP[node["type"]]
        builder.add_node(curr_node, node_func)

    builder.add_node("process_input", process_user_input)
    
    builder.set_entry_point("process_input")

    builder.add_edge("startingPoint-1", "process_input")
    builder.add_conditional_edges("process_input", router)
    
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)
    graph = builder.compile(checkpointer=memory)
    return graph

class ChatBot:
    def __init__(self):
        self.graph = build_graph()
        self.exists = False
    
    def chat(self, user_input: str):
        initial_state = {"messages": []}
        
        if not self.exists:
            initial_state["messages"].append({'role':'system', 'content':"You are an AI chatbot who helps users with their inquiries, issues and requests. Give concise and to the point response."})
            self.exists = True
        elif user_input is not None:
            initial_state["messages"].append({'role':'human', 'content':user_input})

        result = self.graph.invoke(initial_state, {"configurable": {"thread_id": "100"}})
        return result

if __name__ == "__main__":
    chatbot = ChatBot()
    user_input = None
    while True:
        response = chatbot.chat(user_input)
        print("Bot:", response)
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break