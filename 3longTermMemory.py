from langgraph.store.memory import InMemoryStore
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


store = InMemoryStore()

userId = "sour"
userId = userId.lower()
   


@tool
def saveMemory (key:str, value:str)-> str:

       """This tool saves critical pieces of information which is related to the user."""

       namespace = ("users",userId)

       store.put(
              namespace,
              key,
              {
                     "value":value
              }

       )

       return f"Saved memory {key} = {value}"

@tool
def searchMemory() -> str:

       """This tool gets the necessary information about the user from the store"""

       namespace = ("users", userId)

       memory = store.search(namespace)

       if memory is None:
              return "No memory found"
       
       return str(memory)

systemPrompt = """
You are a helpful assistant.

When the user tells you an important personal preference
or fact that could be useful in future conversations,
save it using saveMemory.

When the user asks about information that may be stored
in memory, use searchMemory to retrieve it.

If the user asks what you know about them, search memory
for relevant information before answering.

Do not claim to remember something unless you actually
retrieve it from memory.
"""


model = ChatOllama(
       model = "gpt-oss:20b-cloud",
       temperature=0
)

agent = create_agent(
       model= model,
       tools=[
              saveMemory,
              searchMemory
       ],
       system_prompt= systemPrompt
)

while True:
       userInput = input("User: ")
       if userInput.lower == "exit":
              break

       response = agent.invoke({
              "messgaes":[{
                     "role":"user",
                     "content":userInput
              }]
       })

       print(response["messages"][-1].content)




# this block of code was for testing
# response = agent.invoke({
#        "messages":[{
#               "role":"user",
#               "content":"i like java as my programming language"
#        }]
# })

# print(response["messages"][-1].content)

# memory = store.get(
#        ("users",userId),
#        "preferred_language"
# )

# print(memory)
# print(memory.value if memory else "No Memory")





# response = agent.invoke({
#        "messages":[{
#               "role":"user",
#               "content":"who am i and what is my favorite language"
#        }]
# })


# print(response["messages"][-1].content)





