from typing import TypedDict
from langgraph.graph import START, StateGraph, END


class State(TypedDict):
       message: str

def routerNode(state: State)-> dict:
       return state


def router(state: State)->str:
       if "calculator" in state["message"].lower():
              return "calculator"

       return "chatbot"


def calculator(state: State)->dict:
       return {
              "message": "This is in Calculator"
       }

def chatbot(state: State)->dict:
       return{
              "message":"This is in Chatbot"
       }


graphBuilder = StateGraph(State)


graphBuilder.add_node("router", routerNode)
graphBuilder.add_node("chatbot", chatbot)
graphBuilder.add_node("calculator",calculator)


graphBuilder.add_edge(START, "router")
graphBuilder.add_conditional_edges("router",
                                   router,
                                   {
                                          "calculator":"calculator",
                                          "chatbot":"chatbot"
                                   }
)
print()


graphBuilder.add_edge("calculator", END)
graphBuilder.add_edge("chatbot", END)


graph = graphBuilder.compile()


response=graph.invoke({
       "message":"use the calculator"
})

print(response["message"])