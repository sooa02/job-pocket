import os
import asyncio
from langchain_core.messages import BaseMessage

from exaone_runpod import exaone_infer


def call_runpod_ollama(messages: list[BaseMessage]) -> str:
    """
    Runpod Serverless를 호출하여 Ollama(EXAONE) 추론 결과를 가져옵니다.
    """
    try:
        payload = {"input": {"messages": messages, "temperature": 0.9}}
        result = asyncio.run(exaone_infer(payload))

        if result.get("ok"):
            return result["text"]
        else:
            raise Exception("생성이 제대로 되지 않았습니다.")
    except Exception as e:
        return f"Error: Failed to call Runpod Serverless - {str(e)}"


if __name__ == "__main__":
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 아주 친절한 챗봇입니다. 질문에 잘 답변해주세요"),
            ("human", "{topic}에 대해 자세하게 설명해 주세요."),
        ]
    )
    final_prompt = prompt.invoke({"topic": "LangGraph"})
    input_messages = [
        {"role": "user" if m.type == "human" else m.type, "content": m.content}
        for m in final_prompt.to_messages()
    ]

    print(call_runpod_ollama(input_messages))
