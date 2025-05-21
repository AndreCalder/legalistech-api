import json
import os
from bson import ObjectId, json_util
from controllers.util.gcp_cloudvision import scan_pdf_to_text
from mongoConnection import db
from flask import g
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Content,
    Part,
)
from controllers.util.assistant_config import ASSISTANT_CONFIG
from controllers.eventController import EventController
from controllers.token_balance_controller import Token_Balance_Controller
from datetime import datetime
from tempfile import NamedTemporaryFile
from pinecone.grpc import PineconeGRPC as Pinecone

eventController = EventController()
tkbController = Token_Balance_Controller()

sessions = db["sessions"]
events = db["events"]
sentencias = db["sentencias"]

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("milegalista")


class AssistantController:

    def get_file_ext(self, uploaded_file_filename: str) -> str:
        return uploaded_file_filename.split(".")[-1]

    def flatten_history(self, history_list):
        return "\n".join(
            f"{msg.role.upper()}: {msg.parts[0].text}" for msg in history_list
        )

    def createSession(self, request):
        body = request.json
        body["user_id"] = ObjectId(g.userId)
        body["history"] = []
        body["name"] = "Sesión - " + datetime.now().strftime("%d/%m/%Y")
        savedSession = sessions.insert_one(body).inserted_id

        return str(savedSession)

    def updateSession(self, data):
        session = sessions.find_one_and_update(
            {"_id": ObjectId(data.get("session_id"))},
            {"$set": data},
            upsert=True,
            return_document=True,
        )
        session_id = str(json.loads(json_util.dumps(session))["_id"]["$oid"])
        return {"_id": session_id}, 200

    def getUserSessions(self):
        user_id = g.userId
        userSessions = sessions.find({"user_id": ObjectId(user_id)})
        return json.loads(json_util.dumps(userSessions)), 200

    def getSession(self, id):
        user_id = g.userId
        session = sessions.find_one({"_id": ObjectId(id), "user_id": ObjectId(user_id)})
        return json.loads(json_util.dumps(session)), 200

    def pinecone_consult_logic(query: str):
        query_embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[f"query: {query}"],
            parameters={"input_type": "query"},
        )

        results = index.query(
            namespace="milegalista",
            vector=query_embedding[0].values,
            top_k=15,
            include_values=False,
            include_metadata=True,
        )

        result_arr = []
        for match in results.matches:
            if match.get("score") > 0.79:
                result_arr.append(
                    (
                        f"[{match.metadata.get('documento')}] "
                        f"{match.metadata.get('texto')}"
                    )
                )

        return "\n---\n".join(result_arr[:5])

    def chatSession(self, id, request):

        msg = request.form.get("msg")
        uploaded_file = None
        
        if request.files:
            uploaded_file = request.files["file"]

        message_obj = {
            "role": "user",
            "user_question": msg,
            "timestamp": datetime.now(),
        }

        session = sessions.find_one({"_id": ObjectId(id)})
        history = session.get("history")
        msgHistory = []

        file_data = ""

        for message in history:
            if message.get("role") == "user":
                msgHistory.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(message["user_question"])],
                    )
                )
                if message.get("file_data"):
                    file_data = message.get("file_data")
            elif message.get("role") == "model":
                msgHistory.append(
                    Content(
                        role="model",
                        parts=[Part.from_text(message["bot_response"])],
                    )
                )

        vertexai.init(
            project="mlai-434520",
        )

        generation_config = GenerationConfig(
            temperature=ASSISTANT_CONFIG["LLM"]["TEMPERATURE"]
        )

        model = GenerativeModel(
            ASSISTANT_CONFIG["LLM"]["MODEL"],
            system_instruction=ASSISTANT_CONFIG["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=generation_config,
            tools=[],
        )
        if uploaded_file and uploaded_file.filename:
            ext = self.get_file_ext(uploaded_file.filename).lower()
            if ext == "pdf" or ext == "docx":
                with NamedTemporaryFile() as temp_file:
                    uploaded_file.save(temp_file)
                    temp_file.seek(0)
                    file_data = scan_pdf_to_text(temp_file)
                    message_obj["file_data"] = file_data
            else:
                return {"error": f"Unsupported file format: {ext}"}, 400

        prompt = ASSISTANT_CONFIG["LLM"]["PROMPT"].format(
            MESSAGE=msg, HISTORY=self.flatten_history(msgHistory), FILE_DATA=file_data
        )

        token_count_result = model.count_tokens(prompt)
        estimated_token_cost = token_count_result.total_tokens
        current_balance, _, _ = tkbController.get_token_balance_raw(g.userId)
        token_equivalence = 500

        if (estimated_token_cost / token_equivalence) > current_balance:
            botmsg = (
                "No cuentas con suficientes tokens para realizar esta acción. "
                "Por favor adquiere más tokens o espera a que se "
                "renueven tus tokens mensuales."
            )

            botmsg_object = {
                "role": "model",
                "bot_response": botmsg,
                "timestamp": datetime.now(),
            }

            sessions.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$push": {"history": {"$each": [message_obj, botmsg_object]}}},
                upsert=True,
                return_document=True,
            )

            return json.loads(json_util.dumps(session)), 200
        response = model.generate_content(prompt)

        usage_metadata = response.usage_metadata

        output_tokens = (
            session.get("output_tokens", 0) + usage_metadata.candidates_token_count
        )

        input_tokens = (
            session.get("input_tokens", 0) + usage_metadata.prompt_token_count
        )
        total_token_count = output_tokens + input_tokens

        if len(response.candidates) > 0:
            if len(response.candidates[0].function_calls) == 0:
                botmsg = response.candidates[0].text
                # TODO: Implement function call handling
        else:
            botmsg = response.text

        botmsg_object = {
            "role": "model",
            "bot_response": botmsg,
            "timestamp": datetime.now(),
        }

        token_usage = total_token_count / token_equivalence
        tkbController.use_tokens(g.userId, token_usage)

        updated_session = sessions.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$push": {"history": {"$each": [message_obj, botmsg_object]}},
                "$set": {
                    "output_tokens": output_tokens,
                    "input_tokens": input_tokens,
                    "total_token_count": total_token_count,
                },
            },
            upsert=True,
            return_document=True,
        )

        return json.loads(json_util.dumps(updated_session)), 200
