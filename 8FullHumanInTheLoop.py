from typing_extensions import TypedDict
from typing import Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from langchain_ollama import ChatOllama
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool


class State(TypedDict):
       messages: Annotated[list,add_messages]
       approved: bool


@tool
def multiply(a:float, b:float)->float:
       """This is a tool which takes 2 numbers and multiplies them"""
       return a*b


checkpointer = InMemorySaver()


model = ChatOllama(
       model="gpt-oss:20b-cloud",
       temperature=0
).bind_tools([multiply])

def chatbot(state:State):
       response = model.invoke(state["messages"])

       return{
              "messages": [response]
       }

# approval node

def approvalNode(state:State):
       lastMessage = state["messages"][-1]

       toolCall = lastMessage.tool_calls[0]

       answer = interrupt(
              f"Approve tool call:\n {toolCall['name']}({toolCall['args']})?"
       )


       return{
              "approved":answer
       }

def shouldContinue(state:State):
       lastMessage = state["messages"][-1]

       if lastMessage.tool_calls:
              return "approval"

       return "end"

def afterApproval(state:State):
       if state["approved"] == True:
              return "tools"

       return "end"

config = {
       "configurable":
       {
              "thread_id":"approval-1"
       }
}


toolNode = ToolNode([multiply])


gp = StateGraph(State)

gp.add_node("agent", chatbot)
gp.add_node("approval", approvalNode)
gp.add_node("tools", toolNode)

gp.add_edge(START, "agent")

gp.add_conditional_edges("agent",
                         shouldContinue,
                         {
                                "approval":"approval",
                                "end":END
                         })

gp.add_conditional_edges(

       "approval",
       afterApproval,
       {
              "tools":"tools",
              "end":END
       }

)

graph = gp.compile(checkpointer=checkpointer)

result = graph.invoke({
       "messages":[{
              "role":"user",
              "content":"What is 10 into 10"

       }
              
       ],
       "approved":True
}, config=config)

print("\nGive approval \n")
approval = input("Your approval:")

if (approval=="True"):
       result = graph.invoke(
       Command(resume= True),
       config = config
)
else:
       print("\n Approval was denied")
       



print(result)
print(result["messages"][-1].content)