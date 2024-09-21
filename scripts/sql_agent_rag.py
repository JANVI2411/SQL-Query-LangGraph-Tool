from langchain_community.utilities import SQLDatabase
import sqlite3
import requests
# from api_key import *
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from typing import Any
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langgraph.prebuilt import ToolNode
from langchain.tools import Tool
from pydantic import BaseModel, Field


db = SQLDatabase.from_uri("sqlite:////home/guiseai/edgeops-cicd/database/edgeops.db")

def list_tables(temp: str):
    return db.get_table_names()

def get_schema(table_name: str):
    try:
        return db.get_table_info([table_name])
    except ValueError as e:
        return str(e)

list_tables_tool = Tool(
    name="sql_db_list_tables",
    description="Lists all tables in the SQL database.",
    func=list_tables
)

get_schema_tool = Tool(
    name="sql_db_schema",
    description="Retrieves the schema of a given table from the SQL database.",
    func=get_schema
)

def create_tool_node_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
    """
    Create a ToolNode with a fallback to handle errors and surface them to the agent.
    """
    return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    tool_msgs = []
    for tc in tool_calls:
            tool_msgs.append(ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            ))
            
    return {"messages": tool_msgs}

@tool
def db_query_tool(query: str) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    result = db.run_no_throw(query)
    if not result:
        return "Error: Query failed. Please rewrite your query and try again."
    return result


#PROMPT
query_correction_system = """You are a SQL expert with a strong attention to detail.
                    Double check the SQLite query for common mistakes, including:
                    - Using NOT IN with NULL values
                    - Using UNION when UNION ALL should have been used
                    - Using BETWEEN for exclusive ranges
                    - Data type mismatch in predicates
                    - Properly quoting identifiers
                    - Using the correct number of arguments for functions
                    - Casting to the correct data type
                    - Using the proper columns for joins

                    If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

                    You will call the appropriate tool to execute the query after running this check."""

query_correction_prompt = ChatPromptTemplate.from_messages(
    [("system", query_correction_system), 
     ("placeholder", "{messages}")]
)

query_gen_system = """You are a SQL expert with a strong attention to detail.

                    Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.

                    DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.

                    When generating the query:

                    Output the SQL query that answers the input question without a tool call.

                    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
                    You can order the results by a relevant column to return the most interesting examples in the database.
                    Never query for all the columns from a specific table, only ask for the relevant columns given the question.

                    If you get an error while executing a query, rewrite the query and try again.

                    If you get an empty result set, you should try to rewrite the query to get a non-empty result set. 
                    NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.

                    If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.

                    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""

query_gen_prompt = ChatPromptTemplate.from_messages(
    [("system", query_gen_system), ("placeholder", "{messages}")]
)

class SubmitFinalAnswer(BaseModel):
    """Submit the final answer to the user based on the query results."""

    final_answer: str = Field(..., description="The final answer to the user")


#LLM
query_correction_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools([db_query_tool])
get_schema_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools([get_schema_tool])
list_tables_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools([list_tables_tool])
query_gen_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools([SubmitFinalAnswer])

#CHAINS
query_correction_chain = query_correction_prompt | query_correction_llm
query_gen_chain = query_gen_prompt | query_gen_llm  

if __name__ == "__main__":
    ans = get_schema_tool.invoke("ai_application_catalogue")
    print(ans)


