from .sql_agent_rag import *
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def update_db(abs_path):
    set_db(abs_path)

def model_get_schema(state: State):
    messages = get_schema_llm.invoke(state["messages"])
    return {
        "messages": state["messages"] + [messages],
    }

workflow = StateGraph(State)

# # Add a node for the first tool call
def first_tool_call(state: State): # -> dict[str, list[AIMessage]]:
    messages = AIMessage(content="",tool_calls=[{"name": "sql_db_list_tables",
                                                "args":{"temp":""},
                                                "id": "tool_abcd123"}])
    return {"messages": [messages]}


def query_gen_node(state: State):
    message = query_gen_chain.invoke(state)

    # Sometimes, the LLM will hallucinate and call the wrong tool. We need to catch this and return an error message.
    tool_messages = []
    if message.tool_calls:
        for tc in message.tool_calls:
            if tc["name"] != "SubmitFinalAnswer":
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
                        tool_call_id=tc["id"],
                    )
                )
    else:
        tool_messages = []
    return {"messages": [message] + tool_messages}

def model_correction_query(state: State):
    query = state["messages"][-1]
    messages = query_correction_chain.invoke({"messages": [query]})
    return {"messages": [messages]}

# Define a conditional edge to decide whether to continue or end the workflow
def should_continue(state: State) -> Literal[END, "correct_query", "query_gen"]:
    messages = state["messages"]
    last_message = messages[-1]
    # If there is a tool call, then we finish
    if getattr(last_message, "tool_calls", None):
        # print("-------------DECISION: END-------")
        return END
    if last_message.content.startswith("Error:"):
        # print("-------------DECISION: query_gen-------")
        return "query_gen"
    else:
        # print("-------------DECISION: correct_query-------")
        return "correct_query"

workflow.add_node("first_tool_call", first_tool_call)
workflow.add_node("list_tables_tool", create_tool_node_with_fallback([list_tables_tool]))
workflow.add_node("model_get_schema",model_get_schema)
workflow.add_node("get_schema_tool", create_tool_node_with_fallback([get_schema_tool]))
workflow.add_node("query_gen",query_gen_node)
workflow.add_node("correct_query", model_correction_query)
workflow.add_node("execute_query_tool", create_tool_node_with_fallback([db_query_tool]))

# ValueError: Last message is not an AIMessage
workflow.add_edge(START, "first_tool_call")
workflow.add_edge("first_tool_call", "list_tables_tool")
workflow.add_edge("list_tables_tool", "model_get_schema")
workflow.add_edge("model_get_schema", "get_schema_tool")
workflow.add_edge("get_schema_tool", "query_gen")
workflow.add_conditional_edges("query_gen",should_continue)
workflow.add_edge("correct_query", "execute_query_tool")
workflow.add_edge("execute_query_tool", "query_gen")

app = workflow.compile()

# Give me device_id where the application 'Safety' is deployed
# Give me details for the application 'Safety' from ai_catalogue_application
# query = "Extract Select * from ai_catalogue_application where application_name='Safety';"
# for output in app.stream({"messages": [("user",query )]}):
#     print("\n##################################")
#     print(output)

# messages = app.invoke(
#     {"messages": [("user", "Slect * bucket_data, row_id is 1")]}
# )
# json_str = messages["messages"][-1].tool_calls[0]["args"]["final_answer"]
# print(json_str)

