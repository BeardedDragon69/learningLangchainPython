from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage,ToolMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from typing import  Annotated
from typing_extensions import TypedDict


class State(TypedDict):
       messages: Annotated[list, add_messages]

checkpointer = InMemorySaver()



@tool
def multiply(a:float, b:float)->float:
       """Multiply two numbers"""
       return a*b
@tool
def add(a:float, b:float)->float:
       """Add 2 numbers"""
       return a+b
@tool
def divide(a:float, b:float)->float:
       """divides 2 numbers specifically a/b"""
       return a/b


model = ChatOllama(
       model= "gpt-oss:20b-cloud",
       temperature=0
).bind_tools([multiply,add,divide])

def chatbot(state:State):
       response = model.invoke(state["messages"])

       return{
              "messages":[response]
       }

def shouldContinue(state:State):
       lastMessage = state["messages"][-1]

       if lastMessage.tool_calls:
              return "tools"

       return "end"

config = {
       "configurable":{
              "thread_id":"conversation-1"
       }
}

# def tools(state:State):
#        lastMessage = state["messages"][-1]

#        toolMessages =[]

#        for toolCall in lastMessage.tool_calls:
#               if toolCall["name"] == "multiply":
#                      result = multiply.invoke(
#                             toolCall["args"]
#                      )

#                      toolMessages.append(
#                             ToolMessage(
#                                    content=str(result),
#                                    tool_call_id=toolCall["id"]
#                             )
#                      )

#        return{
#               "messages":toolMessages
#        }

toolNode= ToolNode(
       [
       multiply,
       divide,
       add
       ]
)


graphBuilder = StateGraph(State)
graphBuilder.add_node("chatbot", chatbot)
graphBuilder.add_node("tools",toolNode)


graphBuilder.add_edge(START, "chatbot")
graphBuilder.add_conditional_edges("chatbot",
                                   shouldContinue,
                                   {
                                          "tools":"tools",
                                          "end":END
                                   })
graphBuilder.add_edge("tools","chatbot")

graph = graphBuilder.compile(checkpointer=checkpointer)


response = graph.invoke({
       "messages":[{

              "role":"user",
              "content":"What is 10 multiplied by 20 and divided by 40"

       }
              
       ]
}, config=config)

state = graph.get_state(config)
print("The state =============================")
print(state.values)
print("End of state values after response 1===========================")
print("Response:", response["messages"][-1].content)

response = graph.invoke({
       "messages":[
              {
                     "role":"user",
                     "content":"now multiply that value by 20"
              }
       ]
}, config=config)

state = graph.get_state(config)
print("The state =============================")
print(state.values)
print("End of state values after response ===========================")




print("Response",response["messages"][-1].content)