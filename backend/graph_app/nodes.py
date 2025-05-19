from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from .models import Message

load_dotenv()

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    current_node: int | None
    user_info: dict | None
    user_name: str | None
    next_node: bool

class UserName(BaseModel):
    name: str | None = Field(description="User's name")
    found_name: bool = Field(description="True if we found name, else false")

parser = JsonOutputParser(pydantic_object=UserName)

def starting_point(state: State) -> State:
    messages = state["messages"]
    new_messages = add_messages(messages, AIMessage(content="Hi, I am an AI assistant. How can I help you?"))
    Message.objects.create(content="Hi, I am an AI assistant. How can I help you?", type="bot")
    return {
        **state, 
        "messages": new_messages,
        "current_node": 1,
        "next_node": True
    }

def ask_name(state: State) -> State:
    llm = ChatGroq(model="gemma2-9b-it", temperature=0.1)
    messages = state["messages"]
    if messages and isinstance(messages[-1], HumanMessage) and "user_name" not in state:
        user_response = messages[-1].content
        prompt = PromptTemplate(
            template="Extract the person's name from this input, if present. If no name is found, return 'NONE'. \n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        llm_json = prompt | llm | parser
        try:
            response = llm_json.invoke({"query": user_response})
            result = response
            print("------>",result)
            if "name" in result and result["name"]:
                name = result["name"]
                Message.objects.create(content=f"Thank you, {name}! Let's proceed.", type="bot")
                return {
                    **state,
                    "messages": messages + [AIMessage(content=f"Thank you, {name}! Let's proceed.")],
                    "user_name": name,
                    "current_node": 2,
                    "next_node": True
                }
            else:
                Message.objects.create(content="I didn't catch your name. Could you please share your name?", type="bot")
                return {
                    **state,
                    "messages": messages + [AIMessage(content="I didn't catch your name. Could you please share your name?")],
                    "next_node": False
                }
        except Exception as e :
            print(f"Error: {e}")
            return "Some unexpected error occured."
    else:
        response = llm.invoke(
            messages + [
                HumanMessage(content="Generate a message asking for the user's name. Be friendly and polite.")
            ]
        )
        Message.objects.create(content=response.content, type="bot")
        new_messages = add_messages(messages, AIMessage(content=response.content))
        return {
            **state, 
            "messages": new_messages,
            "current_node": 2,
            "next_node": False
        }

def ask_phone(state: State) -> State:
    llm = ChatGroq(model="gemma2-9b-it", temperature=0.1)
    messages = state["messages"]
    
    # This is a simple implementation - in a real app you might want more robust parsing
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_name = last_user_message.content if last_user_message else "user"
    
    user_info = state.get("user_info", {})
    user_info["name"] = user_name
    
    response = llm.invoke(
        messages + [
            HumanMessage(content=f"Generate a message asking for {user_name}'s phone number. Be friendly and polite.")
        ]
    )
    Message.objects.create(content=response.content, type="bot")
    # Update the state
    new_messages = add_messages(messages, AIMessage(content=response.content))
    return {
        **state, 
        "messages": new_messages,
        "current_node": 3,  # Now we're at the ask phone node
        "user_info": user_info
    }

NODE_MAP = {
    "startingPoint": starting_point,
    "askName": ask_name,
    "askPhone": ask_phone,
}

def generate_router_function(nodes, edges, ):
    node_types = {node["id"]: node["type"]+"-"+node["id"] for node in nodes}
    routing_map = {}
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        routing_map[source_id] = target_id
    
    def router(current_node, get_current=False):
        current_node_id = str(current_node)

        if get_current:
            return node_types.get(current_node_id)

        # Get the target node ID if it exists
        if current_node_id in routing_map:
            target_id = routing_map[current_node_id]
            return node_types.get(target_id, "unknown_node")
        
        # If there's no outgoing edge for this node, it's an end node
        if current_node_id in node_types:
            return END
        
        # If the node ID doesn't exist at all, return the type of the first node
        return node_types.get(next(iter(node_types)), "unknown_node")
    
    return router