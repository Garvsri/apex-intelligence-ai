
from langchain_ollama import ChatOllama
from apex.ai_tools import compare_f1_drivers

# Connect to the local Ollama model
llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0,
)

# Give the model access to our Python analytics tool
llm_with_tools = llm.bind_tools(
    [compare_f1_drivers]
)

question = input("Ask Apex about the 2024 British GP: ")

messages = [
    (
        "system",
        "You are Apex Intelligence AI, an F1 data analyst. "
        "Use compare_f1_drivers for questions comparing drivers. "
        "Never invent statistics. Explain that mean lap times "
        "can be affected by race conditions."
    ),
    ("human", question),
]

try:
    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        messages.append(response)

        for tool_call in response.tool_calls:
            if tool_call["name"] == "compare_f1_drivers":
                result = compare_f1_drivers.invoke(
                    tool_call["args"]
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(result),
                    }
                )

        final_response = llm.invoke(messages)
        print("\nApex:", final_response.content)

    else:
        print("\nApex:", response.content)

except Exception as exc:
    print(f"\nApex encountered an error: {exc}")
    print("Check that Ollama is running and the model is available.")
