from langchain_ollama import ChatOllama



SYSTEMPROMPT = "You are a helpful assistant which greets the user"


model = ChatOllama(

    model = "gpt-oss:20b-cloud",
    temperature= 0.4,
    system_prompt = SYSTEMPROMPT
       
)

response = model.invoke("what is the main difference between langchain and langgraph")
print(response.content)




# agent = create_agent(

#     model = "gpt-oss:20b-cloud",
#     system_prompt = SYSTEMPROMPT
       
# )

# @tool
# def returnName(query: str) -> str:
#        """Returns the name of the user"""

#        return f"Hello your query is {query}"


