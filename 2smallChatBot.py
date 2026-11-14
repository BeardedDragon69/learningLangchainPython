from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver


model = ChatOllama(
       model = "gpt-oss:20b-cloud",
       temperature=0
)


checkpointer = InMemorySaver()

agent = create_agent(
       model = model,
       tools =[],
       checkpointer = checkpointer
)

name =input("Enter your name: ")
name = name.lower()



config = {
       "configurable":{
              "thread_id":name
       }
}

while True:
       userInput = input("You: ")

       if userInput.lower == "exit":
              break

       response = agent.invoke(
              {
                     "messages":[
                            {
                                   "role":"user",
                                   "content":userInput
                            }
                     ]

              },config=config
       )


       print("AI:", response["messages"][-1].content)