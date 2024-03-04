import requests
from transformers import AutoTokenizer
import logging

logging.basicConfig(
    filename="lmstudio-server-log.txt",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


def bot_gpt(task: str, answer="") -> str:

    system_content = "Давай краткий ответ с решением на русском языке"
    assistant_content = "Решим задачу по шагам: " + answer
    temperature = 1
    max_tokens = 64

    response = requests.post(

        "http://localhost:1234/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "messages": [
                {"role": "user", "content": task},
                {"role": "system", "content": system_content},
                {"role": "assistant", "content": assistant_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )
    if response.status_code == 200:
        result = response.json()["choices"][0]["message"]["content"]
        print("Ответ получен!")
        logging.debug(f"Отправлено: {task}\nПолучен результат: {result}")
        return result
    else:
        print("Не удалось получить ответ :(")
        logging.error(f"Отправлено: {task}\nПолучена ошибка: {response.json()}")


def count_tokens(text):
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")
    return len(tokenizer.encode(text))