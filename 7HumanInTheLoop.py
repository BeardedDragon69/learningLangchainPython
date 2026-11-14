from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
       message: str
       approved: bool

checkpointer = InMemorySaver()

config = {
       "configurable":{
              "thread_id":"approval-1"
       }
}



def approvalNode(state:State):
       answer = interrupt(
              f"Do you approve this operation: {state['message']}?"
       )

       return{
              "message":state['message'],
              "approved": answer
       }

graphBuilder = StateGraph(State)

graphBuilder.add_node("approval", approvalNode)
graphBuilder.add_edge(START, "approval")
graphBuilder.add_edge("approval", END)

graph = graphBuilder.compile(
       checkpointer=checkpointer
)

result = graph.invoke({
       "message":"Delete the account",
       "approved":True
},config=config)


print(result)
