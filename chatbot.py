from ai_helper import get_ai_response
from database import save_chat_history, save_unknown_question


def get_bot_response(user_id, user_message):
    try:
        bot_response = get_ai_response(user_message)

        if not bot_response:
            bot_response = "Sorry, I could not generate a response."
            save_unknown_question(user_id, user_message)

    except Exception as e:
        bot_response = f"AI Error: {str(e)}"
        save_unknown_question(user_id, user_message)

    save_chat_history(user_id, user_message, bot_response)

    return bot_response