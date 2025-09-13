import os
from typing import Optional, Any
from dotenv import load_dotenv
from openai import RateLimitError, APIConnectionError, APIStatusError
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

# DEFAULT_OPENROUTER_MODEL = os.getenv("LLM_DEFAULT_MODEL", "qwen/qwen-2.5-72b-instruct")
# OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
# OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")



DEFAULT_COMET_MODEL = os.getenv("DEFULT_COMET_MODEL")
COMET_API_KEY = os.getenv("COMET_API_KEY")
COMETAPI_BASE_URL: str = os.getenv("COMETAPI_BASE_URL", "https://api.cometapi.com/v1")



API_NOT_INITIALIZED_ERROR = "[ОШИБКА API] Клиент OpenRouter не инициализирован."
API_RATE_LIMIT_ERROR = "[ОШИБКА API] Превышен лимит запросов к API."
API_CONNECTION_ERROR = "[ОШИБКА API] Не удалось подключиться к API."
API_GENERAL_ERROR = "[ОШИБКА API] Произошла ошибка при обращении к API."


def call_llm(prompt_text, system_instruction = "", model = DEFAULT_COMET_MODEL, temperature = 0):
    if not COMET_API_KEY:
        return API_NOT_INITIALIZED_ERROR

    try:
        llm = ChatOpenAI(
            base_url=COMETAPI_BASE_URL,
            api_key=COMET_API_KEY,
            model=model,
            temperature=temperature,
        )

        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt_text))

        response = llm.invoke(messages)
        return response.content.strip()

    except RateLimitError:
        return API_RATE_LIMIT_ERROR
    except APIConnectionError:
        return API_CONNECTION_ERROR
    except APIStatusError as e:
        return f"{API_GENERAL_ERROR} (Статус: {e.status_code})"
    except Exception as e:
        return f"{API_GENERAL_ERROR} {e}"


def call_qwen(user_prompt, system_instruction = ''):
    return call_llm(
        prompt_text=user_prompt,
        system_instruction=system_instruction
    )


if __name__ == "__main__":
    # if not OPENROUTER_API_KEY:
    #     print("Ключ API OpenRouter (OPENROUTER_API_KEY) не найден в переменных окружения.")
    # else:
    #     print("Ключ API загружен.")

    user_question = "Who are you? Who is your creator?"
    system_prompt = "Answer like a Rust Cohle from True Detective"

    answer = call_qwen(user_prompt=user_question, system_instruction=system_prompt)

    print("------------" * 50)
    print("Ответ модели:")
    print(answer)
    print("------------" * 50)
