from typing import Annotated
from typing_extensions import TypedDict


from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END, START




from langchain_core.tools import tool
from langchain_ollama import ChatOllama











class State(TypedDict):
       messages: Annotated[list, add_messages]
       approved: bool


@tool
def multiply(a: float, b:float):
       """This is a tool which takes in 2 numbers and multiplies them and returns the product"""
       return a*b


@tool
def division(a:float, b:float):
       """This is a tool which returns the quotient when a is divided by b"""
       return a/b

@tool
def addition(a:float, b:float):
       """This is a tool which returns the sum of two numbers a and b"""
       return a+b


@tool
def subtraction(a:float, b:float):
       """This is a tool which returns the difference of a and b(a-b)"""
       return a-b

tools = [multiply, addition, division, subtraction]
model = ChatOllama(
       temperature=0,
       model="gpt-oss:20b-cloud"
).bind_tools(tools)


def approvalNode(state:State):
       lastMessage = state["messages"][-1]
       toolCalls = lastMessage.tool_calls

       approvalDetails = "\n".join(
              f"{i+1}, {call['name']}({call['args']})"
              for i, call in enumerate(toolCalls)
       )

       answer = interrupt(
              f"Approve ALL these tool calls? \n\n{approvalDetails}"
       )

       return {"approved": answer}

def shouldContinue(state:State):
       lastMessage = state["messages"][-1]

       if lastMessage.tool_calls:
              return "approval"
       return "end"

def afterApproval(state:State):
       if(state["approved"]):
              return "tools"

       return "end"

def agent(state:State):
       response = model.invoke(state["messages"])


       return {
              "messages":[response]
       }

checkPointer = InMemorySaver()

toolNode = ToolNode(tools)

builder = StateGraph(State)

builder.add_node("agent", agent)
builder.add_node("approval", approvalNode)
builder.add_node("tools", toolNode)

builder.add_edge(START, "agent")


builder.add_conditional_edges("agent", 
                              shouldContinue,
                              {
                                     "approval":"approval",
                                     "end": END
                              }
)

builder.add_conditional_edges("approval",
                               afterApproval,
                               {
                                      "tools":"tools",
                                      "end": END
                               }
)


builder.add_edge("tools", "agent")

graph = builder.compile(checkpointer=checkPointer)

config ={
       "configurable":{
              "thread_id": "batch-approval-1"
       }
}

result = graph.invoke(
    {
        "messages": [
               {
                "role": "system",
                "content": """
                You are a calculator agent.

                IMPORTANT RULES:
                1. You MUST use the available calculator tools
                   for every arithmetic operation.
                2. Never calculate arithmetic mentally.
                3. If multiple operations are requested,
                   execute them in the correct order.
                4. After receiving a tool result, use another
                   tool if more arithmetic operations remain.
                5. Only provide the final answer after all
                   operations have been completed using tools.
                """
            },
            {
                "role": "user",
                "content": "Calculate 10 multiplied by 20 then divide by 30 and finally subtract 20"
            }
        ],
        "approved": False
    },
    config=config
)


while result.get("__interrupt__"):
       print(result["__interrupt__"][0].value)

       approval = input("\n Approve all tool calls?(yes/no): ")
       decision = approval.strip().lower()

       if decision in ("yes", "y"):
              result = graph.invoke(
                     Command(resume=True),
                     config = config
              )
       elif decision in("no", "n"):
              result = graph.invoke(
                     Command(resume = False),
                     config = config
              )
       else:
              print("Invalid Input. The graph remains paused.")
              result = None

if result is not None:
       print(result)

       if not result.get("__interrupt__"):
              print("Final Message: ", result["messages"][-1].content)
