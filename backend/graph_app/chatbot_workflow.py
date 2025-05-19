from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated
from langchain_core.messages import AIMessage, SystemMessage
import sqlite3, os
from .nodes import NODE_MAP, generate_router_function
from .models import Message

class Chatbot:
    def __init__(self, Nodes, Edges):
        self.nodes = Nodes
        self.edges = Edges
        self.exists = False
        self.graph = self.build_graph(Nodes)

    class State(TypedDict):
        messages: Annotated[list[AnyMessage], add_messages]
        current_node: int | None
        user_info: dict | None
        user_name: str | None
        next_node: bool
    
    def process_user_input(self, state: State) -> State:
        return state

    def router(self, state: State):
        current_node = state["current_node"] if "current_node" in state else 0
        getNext = generate_router_function(self.nodes, self.edges)
        if current_node == 2 and "user_name" not in state:
            return getNext(current_node, get_current=True)
        next_node = getNext(current_node)
        return next_node

    def run_next_node(self, state: State):
        if state["next_node"]:
            current_node = state["current_node"] if "current_node" in state else 0
            getNext = generate_router_function(self.nodes, self.edges)
            next_node = getNext(current_node)
            state["next_node"] = False
            return next_node
        else:
            state["next_node"] = False
            return END
    
    def build_graph(self, Nodes):
        builder = StateGraph(self.State)
        
        for node in Nodes:
            curr_node = node["type"] + "-" + node["id"]
            node_func = NODE_MAP[node["type"]]
            builder.add_node(curr_node, node_func)
            builder.add_conditional_edges(curr_node, self.run_next_node)

        builder.add_node("process_input", self.process_user_input)
        
        builder.set_entry_point("process_input")

        builder.add_conditional_edges("process_input", self.router)
        
        conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        memory = SqliteSaver(conn)
        self.graph = builder.compile(checkpointer=memory)
        if not check_thread_id_exists():
            self.get_response(None)
        return self.graph
    
    def get_response(self, user_input: str):
        initial_state = {"messages": [], "next_node": False}
        
        if not check_thread_id_exists():
            initial_state["messages"].append({'role':'system', 'content':"You are an AI chatbot who helps users with their inquiries, issues and requests. Give concise and to the point response."})
        elif user_input is not None:
            Message.objects.create(content=user_input, type="user")
            initial_state["messages"].append({'role':'human', 'content':user_input})

        result = self.graph.invoke(initial_state, {"configurable": {"thread_id": "101"}})
        print('--------------')
        print("Bot:", result)
        print('--------------')
        return result["messages"][-1].content

import os
def check_thread_id_exists(db_path="checkpoints.sqlite"):
    try:
        if not os.path.isfile(db_path):
            return False
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # cursor.execute("""
        #     SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints';
        # """)
        # if not cursor.fetchone():
        #     return False
        try:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM checkpoints WHERE thread_id = ?)", (101,))
        except Exception  as e:
            print(f"Errrrorrr: {e}")
            return False
        # Fetch the result (1 if exists, 0 if not)
        exists = cursor.fetchone()[0]
        conn.close()
        return bool(exists)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise