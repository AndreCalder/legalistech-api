import json
import vertexai
from vertexai.generative_models import GenerativeModel
from controllers.util.sentence_processing import SENTENCE_CONFIG


def process_sentence(sentence):

    vertexai.init(
        project="mlai-434520",
    )

    model = GenerativeModel(
        SENTENCE_CONFIG["LLM"]["MODEL"],
        system_instruction=SENTENCE_CONFIG["LLM"]["SYSTEM_INSTRUCTION"],
        generation_config={"temperature": SENTENCE_CONFIG["LLM"]["TEMPERATURE"]},
    )

    chat = model.start_chat(response_validation=False)

    prompt = SENTENCE_CONFIG["LLM"]["PROMPT"].format(TEXT=sentence)

    response = chat.send_message(prompt)
    cleaned_response_text = (
        response.text.replace("```json", "").replace("```", "").strip()
    )
    response_json = json.loads(cleaned_response_text)
    return response_json
