import json
import os
from bson import ObjectId, json_util
from controllers.util.gcp_cloudvision import scan_pdf_to_text
from controllers.util.toolkit_funcs import (
    search_tool,
)
from mongoConnection import db
from flask import g
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Content,
    Part,
)
from controllers.util.assistant_config import ASSISTANT_CONFIG
from controllers.util.mongo_assistant_config import MONGO_ASSISTANT_CONFIG

from controllers.eventController import EventController
from controllers.token_balance_controller import Token_Balance_Controller
from datetime import datetime
from tempfile import NamedTemporaryFile
from pinecone.grpc import PineconeGRPC as Pinecone
from dotenv import load_dotenv
from controllers.consultController import ConsultController

credentials = service_account.Credentials.from_service_account_file(
    "controllers/util/service_key.json"
)

load_dotenv()

vertexai.init(project="mlai-434520", credentials=credentials)

consultController = ConsultController()
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
        body["created_at"] = datetime.now()
        body["updated_at"] = datetime.now()

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

    def pinecone_consult_logic(self, query: str):
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
                    f"[{match.metadata.get('documento')}] {match.metadata.get('texto')}"
                )

        return "\n---\n".join(result_arr[:5])

    def chatSession(self, id, request):
        msg = request.form.get("msg")
        uploaded_file = request.files.get("file") if request.files else None

        message_obj = {
            "role": "user",
            "user_question": msg,
            "timestamp": datetime.now(),
        }

        if uploaded_file:
            message_obj.update(
                {
                    "file_url": request.form.get("file_url"),
                    "file_name": request.form.get("file_name"),
                    "file_type": request.form.get("file_type"),
                }
            )

        session = sessions.find_one({"_id": ObjectId(id)})
        history = session.get("history", [])
        msgHistory = []
        file_data = ""

        for message in history:
            if message.get("role") == "user":
                msgHistory.append(
                    Content(
                        role="user", parts=[Part.from_text(message["user_question"])]
                    )
                )
                file_data = message.get("file_data")
            elif message.get("role") == "model":
                msgHistory.append(
                    Content(
                        role="model", parts=[Part.from_text(message["bot_response"])]
                    )
                )

        generation_config = GenerationConfig(
            temperature=ASSISTANT_CONFIG["LLM"]["TEMPERATURE"]
        )

        model_cfg = ASSISTANT_CONFIG
        model = GenerativeModel(
            model_cfg["LLM"]["MODEL"],
            system_instruction=model_cfg["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=generation_config,
            tools=[search_tool],
        )
        prompt_template = model_cfg["LLM"]["PROMPT"]

        if uploaded_file and uploaded_file.filename:
            ext = self.get_file_ext(uploaded_file.filename).lower()
            if ext in ["pdf", "docx"]:
                with NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
                    uploaded_file.save(temp_file)
                    temp_path = temp_file.name

                try:
                    file_data = scan_pdf_to_text(temp_path)
                    message_obj["file_data"] = file_data
                finally:
                    os.remove(temp_path)
            else:
                return {"error": f"Unsupported file format: {ext}"}, 400

        prompt = prompt_template.format(
            MESSAGE=msg, HISTORY=self.flatten_history(msgHistory), FILE_DATA=file_data
        )

        token_count_result = model.count_tokens(prompt)
        estimated_token_cost = token_count_result.total_tokens
        current_balance, _, _ = tkbController.get_token_balance_raw(g.userId)

        token_equivalence = 500

        if (estimated_token_cost / token_equivalence) > current_balance:
            botmsg = (
                "No cuentas con suficientes tokens para realizar esta acción. "
                "Por favor adquiere más tokens o espera a que se renueven tus tokens mensuales."
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

        # Teoría André: Necesitamos que el modelo identifique si se debe invocar una herramienta más de una vez,
        # posiblemente sea en response.candidates[0].function_calls, y debamos iterar sobre esa lista, en caso de iterar,
        # vamos a tener que juntar las respuestas de las herramientas en un solo mensaje para procesar en un solo prompt (linea 254)
        # EJ:
        # Que cualquier escenario se pueda resolver con 2 llamadas
        # Pinecone para búsuqeda de artículos, legislación y jurísprudencias 
        # *Posibles mejoras: Tener la capacidad de buscar múltiples artículos a la vez 
        # Mongo para consulta de sentencias *Posibles mejoras: Múltiples tipos de caso, proponer idea de mejora de rendimiento
        """
            function_calls: [
                {
                    name: "combined_legal_search",
                    args: {
                        source: "pinecone",
                        ...
                    }
                },
                {
                    name: "combined_legal_search",
                    args: {
                        source: "mongo_sentencias",
                        ...
                    }
                }
            ]
        """
        
        call = (
            response.candidates[0].function_calls[0]
            if response.candidates and response.candidates[0].function_calls
            else None
        )

        if call:
            if call.name == "combined_legal_search":
                if call.args.get("source") == "pinecone":
                    # Posible solución para múltiples artículos: Convertir los argumentos en un arreglo de objetos e iterar sobre ellos dentro de la función
                    # Cambiar system_instructions en el assistant_config para que pueda identificar multiples artículos y documentos en caso de ser necesario
                    res = consultController.search(
                        call.args.get("article"),
                        call.args.get("article_id"),
                        call.args.get("document"),
                        call.args.get("k_count"),
                    )
                    tool_result_text = (
                        f"Resultado de la herramienta pinecone_consult:\n{res}"
                    )
                elif call.args.get("source") == "mongo_sentencias":
                    res = consultController.search_mongo_sentencias(
                        case_type=call.args.get("case_type", ""),
                        user_request=message_obj,
                    )
                tool_result_text = res

            else:
                tool_result_text = "La herramienta invocada no está implementada."

            msgHistory.append(
                Content(role="tool", parts=[Part.from_text(tool_result_text)])
            )

            prompt = prompt_template.format(
                MESSAGE="Tool result received, please provide a follow-up response.",
                HISTORY=self.flatten_history(msgHistory),
                FILE_DATA="",
            )
            response = model.generate_content(prompt)
            botmsg = (
                response.text
                if hasattr(response, "text") and response.text
                else "Respuesta generada por herramienta."
            )
        else:
            botmsg = (
                response.text
                if hasattr(response, "text") and response.text
                else "Respuesta generada."
            )

        botmsg_object = {
            "role": "model",
            "bot_response": botmsg,
            "timestamp": datetime.now(),
        }

        if message_obj.get("file_data"):
            from controllers.util.sentence_config import extract_fields_from_text

            analysis = extract_fields_from_text(message_obj["file_data"])

            def default_if_empty(value):
                if isinstance(value, list) and not value:
                    return ["No relevant data found for this field"]
                if isinstance(value, dict) and all(not v for v in value.values()):
                    return {k: "No relevant data found for this field" for k in value}
                if isinstance(value, str) and not value:
                    return "No relevant data found for this field"
                return value

            analysis = {k: default_if_empty(v) for k, v in analysis.items()}

            sentence_doc = {
                "user_id": ObjectId(g.userId),
                "session_id": ObjectId(id),
                "file_name": message_obj.get("file_name"),
                "file_data": message_obj.get("file_data"),
                **analysis,
                "timestamp": datetime.now(),
            }
            sentencias.insert_one(sentence_doc)

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
