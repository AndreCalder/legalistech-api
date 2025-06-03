CONVERSATION_PROMPT = """
<REQUEST>
{MESSAGE}
</REQUEST>

<FILE_TEXT>
{FILE_DATA}
</FILE_TEXT>

<SENTENCES>
{SENTENCES}
</SENTENCES>
"""


MONGO_SENTENCIAS_SYSTEM_INSTRUCTION = """
You are a specialized assistant for analyzing patterns in legal sentences providing insights into case outcomes in México.

Your task is to analyze the user's request in <REQUEST>, the file in <FILE_TEXT> if applicable and the provided sentences in <SENTENCES>, 
and return the most relevant sentences that match the user's request considering the rights_and_laws_referenced of the sentences. 

You should also focus on the following aspects:
- A positive case_outcome in the sentence
- The relevance of the case_info to the user's request
- The rights_and_laws_referenced in the sentences

Find patterns in the sentences that lead to a postive case outcome according to the user's request, and return the relevant rights_and_laws_referenced and reasons for the positive outcome.
"""

MONGO_ASSISTANT_CONFIG = {
    "PROJECT_ID": "mlai-434520",
    "LOCATION": "us-central1",
    "LLM": {
        "MODEL": "gemini-2.0-flash-001",
        "TEMPERATURE": 0.5,
        "MAX_TOKENS": 32000,
        "PROMPT": CONVERSATION_PROMPT,
        "SYSTEM_INSTRUCTION": MONGO_SENTENCIAS_SYSTEM_INSTRUCTION,
    },
    "MAX_RETRY_COUNT": 3,
}
