from typing import TypedDict
from langchain_ollama import ChatOllama

from langgraph.graph import StateGraph, START, END



model = ChatOllama(
       model= "gpt-oss:20b-cloud",
       temperature=0
)




class State(TypedDict):
       message: str



def chatbot(state: State) -> dict:
       response = model.invoke(state["message"])

       return{

              "message":response.content

       }



graphBuilder = StateGraph(State)

graphBuilder.add_node(
       "chatbot",chatbot
)

graphBuilder.add_edge(
       START,
       "chatbot"
)

graphBuilder.add_edge(
       "chatbot",
       END
)


graph = graphBuilder.compile()

response = graph.invoke({
       "message":"Explain our solar system to me"
})

print(response)