import telebot
import logging
from telebot.types import ReplyKeyboardMarkup, Message
from dotenv import load_dotenv
from os import getenv
from main import load_data, save_data
from gpt import bot_gpt, count_tokens

load_dotenv()
bot = telebot.TeleBot(getenv('TOKEN'))
user_data = load_data()

logging.basicConfig(
    filename="lmstudio-server-log.txt",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


@bot.message_handler(commands=['start'])
def start_command(message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    if str(user_id) not in user_data:

        user_data[str(user_id)] = {
              "user_name": message.from_user.username,
              "question": None,
              "answer": None
        }

        save_data(user_data)

    bot.send_message(message.from_user.id, reply_markup=create_keyboard(["Задать новый вопрос"]),
                     text=f"Приветствую тебя, {user_name}!\n"
                          f"Нажми на кнопку для вопроса!")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.from_user.id, text="Я твой цифровой собеседник. "
                                                "Узнать обо мне подробнее можно командой /about")


@bot.message_handler(commands=['about'])
def about_command(message):
    bot.send_message(message.from_user.id, text="Рад, что ты заинтересован_а! Мое предназначение — "
                                                "не оставлять тебя в одиночестве и всячески подбадривать!")


def filter_solve_task(message: Message) -> bool:
    return message.text == "Задать новый вопрос"


@bot.message_handler(func=filter_solve_task)
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши условие задачи:")
    bot.register_next_step_handler(message, answer)


@bot.message_handler(content_types=['text'])
def answer(message):
    user_id = message.chat.id
    user_data[str(user_id)]['question'] = message.text
    save_data(user_data)
    bot.register_next_step_handler(message, give_answer)


def give_answer(message: Message):
    user_id = message.chat.id
    if count_tokens(message.text) <= 300:
        bot.send_message(message.chat.id, "Решаю...")
        answer = bot_gpt(message.text)
        user_data[str(user_id)]["answer"] = answer
        save_data(user_data)

        if answer is None:
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        elif answer == "":
            bot.send_message(
                user_id,
                "Не могу сформулировать решение :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )

        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать новый вопрос", "Продолжить объяснение"]
                ),
            )

    else:
        user_data[str(user_id)]["question"] = None
        user_data[str(user_id)]["answer"] = None
        save_data(user_data)

        bot.send_message(
            message.chat.id,
            "Текст задачи слишком длинный. Пожалуйста, попробуй его укоротить.",
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Текст задачи слишком длинный"
        )


def filter_continue_explaining(message: Message) -> bool:
    return message.text == "Продолжить объяснение"


@bot.message_handler(func=filter_continue_explaining)
def continue_explaining(message: Message):
    user_id = message.chat.id

    if not user_data[str(user_id)]["question"]:
        bot.send_message(
            user_id,
            "Для начала напиши условие задачи:",
            reply_markup=create_keyboard(["Задать новый вопрос"]),
        )

    else:
        bot.send_message(user_id, "Формулирую продолжение...")
        answer = bot_gpt(user_data[str(user_id)]["question"])
        user_data[str(user_id)]["answer"] += answer
        save_data(user_data)

        if answer is None:
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        elif answer == "":
            bot.send_message(
                user_id,
                "Задача полностью решена ^-^",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать новый вопрос", "Продолжить объяснение"]
                ),
            )


def create_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=["debug"])
def send_logs(message: Message):
    with open("lmstudio-server-log.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


bot.polling(none_stop=True)