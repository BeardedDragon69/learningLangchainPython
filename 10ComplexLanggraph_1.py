from langgraph.graph import END, START, StateGraph
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict as td
from langchain_core.tools import tool

from pydantic import BaseModel
from typing import Optional


# dummy data

productVersion = {

       "langchain": "0.3.27",
       "langgraph": "0.6.5",
       "langchain4j": "1.2.0"

}

productDocumentation = {
    ("langchain", "0.3.27"):
        "LangChain documentation: Chains, tools, agents and retrieval.",

    ("langgraph", "0.6.5"):
        "LangGraph documentation: StateGraph, nodes, edges, persistence and agents.",

    ("langchain4j", "1.2.0"):
        "LangChain4j documentation: AI services, tools, memory and agents."
}

productError ={

       ("langgraph","python","Code:400"): "Fix the thing in your code",
       ("langchain","python","Code:404"): "Not found, try looking at the schemas",
       ("langchain4j","java","Code:500"): "The service is not available, try restarting the service" 

}


class SupportState(td):
       userRequest: str
       category: str
       response: str
       agentResponse: str


# define the chat model 

model = ChatOllama(
      model="gpt-oss:20b-cloud",
      temperature=0
)

# defining the structured output class

class TechnicalRequest(BaseModel):
       language: str[Optional] = None
       productName: str[Optional] = None
       version: float[Optional] = None
       errorCode: int[Optional] = None
       


# the system messages


systemMessageClassifier = """

You are a classifier who can classify a user question into either of the following three categories:
       1. billing: if a user asks anything requiring financial or billing related queries.
       2. technical: if a user asks any technical questions related to any product specification or anything related to langchain, langgraph or AI.
       3. general: if a user asks a question and if it does not fit billing or technical description, then you classify it as general.
You are to classify it in the above 3 categories only and nothing else

"""

systemMessageBilling = """

       You are an expert at billing related issues, use the necessary tools to solve the user request.
       For now just return to the user that your billing issue is solved.

"""

systemMessageTechnical = """

       You are an expert at technical related issues, use the necessary tools to solve the user request.
       For now just return to the user that your technical issue is solved.

"""

systemMessageGeneral = """

       You are an expert at general issues, use the necessary tools to solve the user request.
       For now just return to the user that your general issue is solved.

"""

# the tool classes


# the technical tools

@tool
def getProductVersion(productName: str)-> str:

       """Returns the version of the product"""

       product = productName.lower()
       if product not in productVersion:
              return f"{productName} not in the data list"

       return productVersion[product]



@tool
def  searchDocumentationTool(productName)->str:

       """Returns the product docuementation for a particular productName and Version"""

       # for now it fetches only for the product name later make it such that it fetches for a product version too
       productVersion = getProductVersion(productName)
       key = (productName.lower(), productVersion)
       if key not in productDocumentation:
              return f"Documentation not found for {productName}"
       return productDocumentation[key]


@tool
def diagnoseError(productName, language, errorCode)->str:

       """Return the diagnosis for the error code"""
       productVersion = getProductVersion(productName)
       key = (productName.lower(), language.lower(), errorCode)

       if key not in productError:
              return f"The {errorCode} is not there for the product:{productName} in {language} for the version:{productVersion}"
       return productError[key]





# the agents 


def classifierNode(state: SupportState):

    userRequest = state["userRequest"].lower()
    category = model.invoke([
       {
        "role":"system",
        "content": systemMessageClassifier
       },
       {
             "role": "user",
             "content":userRequest
       }
    ]).content.strip().lower()
    print(category)

    

    validCategories = ["billing", "technical", "general"]

    if category not in validCategories:
           raise ValueError(f"Not a valid category {category}")
           
           


    return {"category": category}


def technicalNode(state: SupportState):
       # so what i need to do is take the user request and see what all tools will i require and use them
       userRequest = state["userRequest"]

       technicalExtractor = model.with_structured_output(TechnicalRequest)



       response = model.invoke([
              {
                     "role":"system",
                     "content": systemMessageTechnical
              },
              {
                     "role": "user",
                     "content": userRequest
              }
       ]).content


       category = state["category"]
       print(f"your response was routed to the {category} category")

       return{"agentResponse": response}
       

       

def billingNode(state: SupportState):

       userRequest = state["userRequest"]

       response = model.invoke([
                            {
                                   "role":"system",
                                   "content": systemMessageBilling
                            },
                            {
                                   "role": "user",
                                   "content": userRequest
                            }
       ]).content

       category = state["category"]
       print(f"your response was routed to the {category} category")
       return {"agentResponse":response}


def generalNode(state: SupportState):

       userRequest = state["userRequest"]

       response = model.invoke([
                            {
                                   "role":"system",
                                   "content": systemMessageGeneral
                            
                            },
                            {
                                   "role": "user",
                                   "content": userRequest
                            }
       ]).content

       category = state["category"]
       print(f"your response was routed to the {category} category")
       return {"agentResponse":response}


def supervisorNode(state: SupportState):
       agentResponse= state["agentResponse"]

       return{"response": agentResponse}


       


def responseNode(state: SupportState):
       category = state["category"]

       if category == "technical":
              return {"response": "You are in the technical node function"}

       if category == "billing":
              return {"response": "You are in the billing node function"}

       else:
             return {"response": "You are in the general node function"}
             

def routerFunction(state:SupportState):
       return state["category"]

#  now building the graph

builder = StateGraph(SupportState)

builder.add_node("ClassifierNode", classifierNode)
builder.add_node("TechnicalNode", technicalNode)
builder.add_node("BillingNode", billingNode)
builder.add_node("ResponseNode", responseNode)
builder.add_node("GeneralNode", generalNode)
builder.add_node("SupervisorNode", supervisorNode)

builder.add_edge(START, "ClassifierNode")
builder.add_conditional_edges("ClassifierNode",
                              routerFunction,
                              {
                                     "billing":"BillingNode",
                                     "technical":"TechnicalNode",
                                     "general": "GeneralNode"
                              }
                            )

builder.add_edge("BillingNode", "SupervisorNode")
builder.add_edge("TechnicalNode", "SupervisorNode")
builder.add_edge("GeneralNode", "SupervisorNode")

builder.add_edge("SupervisorNode", END)

grpah = builder.compile()
result = grpah.invoke({
       
       "userRequest":"I am having difficulty in billing customers"
       })

print(result["response"])



       