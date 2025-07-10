# controllers/assistantController.py
import json
import os
from bson import ObjectId, json_util
from flask import g, Response, stream_with_context
from datetime import datetime
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, GenerationConfig, Content, Part
import vertexai
from io import BytesIO
from controllers.util.gcp_cloudvision import scan_pdf_to_text
from controllers.util.toolkit_funcs import search_tool, clear_history
from controllers.util.assistant_config import ASSISTANT_CONFIG
from controllers.util.mongo_assistant_config import MONGO_ASSISTANT_CONFIG
from controllers.eventController import EventController
from controllers.token_balance_controller import Token_Balance_Controller
from controllers.consultController import ConsultController
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from mongoConnection import db

# Inicializa credenciales para Vertex AI
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

    def reset_session(self, session_id):
        try:
            result = sessions.update_one(
                {"_id": ObjectId(session_id)}, {"$set": {"history": []}}
            )
            if result.modified_count > 0:
                return {"message": "Session history reset successfully."}, 200
            else:
                return {"message": "Session not found or already empty."}, 404
        except Exception as e:
            return {"error": f"Error resetting session: {str(e)}"}, 500

    def getUserSessions(self):
        user_id = g.userId
        userSessions = sessions.find({"user_id": ObjectId(user_id)})
        return json.loads(json_util.dumps(userSessions)), 200

    def getSession(self, id):
        user_id = g.userId
        session = sessions.find_one({"_id": ObjectId(id), "user_id": ObjectId(user_id)})
        return json.loads(json_util.dumps(session)), 200

    def process_call(self, i, call):
        start_time = datetime.now()
        local_tool_result = ""
        local_debug = ""

        if call.name == "combined_legal_search":
            if call.args.get("source") == "pinecone":
                k_val = call.args.get("k_count", 5)
                res = consultController.search(
                    query=call.args.get("article"),
                    id=call.args.get("article_id"),
                    document=call.args.get("document"),
                    k_count=k_val,
                )
                exact = res.get("exact_match")
                similars = res.get("similar_matches", [])

                section = (
                    f"\n[{i+1}] Resultado para artículo {call.args.get('article')}:\n"
                )
                if exact:
                    section += f"Coincidencia exacta:\n- ID: {exact.get('id')}\n- Texto: {exact['metadata'].get('texto', '')[:500]}...\n\n"
                else:
                    section += "No se encontró coincidencia exacta.\n\n"

                if similars:
                    section += "Artículos relacionados:\n"
                    for idx, match in enumerate(similars):
                        section += f"{idx+1}. ID: {match.get('id')} — {match['metadata'].get('texto', '')[:300]}...\n"
                else:
                    section += "No se encontraron artículos similares relevantes.\n"
                local_tool_result = section + "\n---"

        elif call.name == "reset_session_history":
            session_id = call.args.get("session_id", id)
            if isinstance(session_id, str) and len(session_id) == 24:
                owner_session = sessions.find_one(
                    {"_id": ObjectId(session_id), "user_id": ObjectId(g.userId)}
                )
                if owner_session:
                    reset_result, status = self.reset_session(session_id)
                    local_tool_result = f"\n[{i+1}] {reset_result.get('message')}\n---"
                    duration = (datetime.now() - start_time).total_seconds()
                    local_debug = f"Llamada {i+1}: {duration:.2f}s"
                    return i, local_tool_result, local_debug
            local_tool_result = f"\n[{i+1}] Error: Permiso denegado o ID inválido.\n---"

        else:
            local_tool_result = f"\n[{i+1}] Función '{call.name}' no implementada.\n---"

        duration = (datetime.now() - start_time).total_seconds()
        local_debug = f"Llamada {i+1}: {duration:.2f}s"
        return i, local_tool_result, local_debug

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
        if session is None:
            history = []
            session_output_tokens = 0
            session_input_tokens = 0
        else:
            history = session.get("history", [])
            session_output_tokens = session.get("output_tokens", 0)
            session_input_tokens = session.get("input_tokens", 0)

        msgHistory = []
        file_data = ""

        # Leer el mensaje y generar un titulo para la sesión (Guardar en DB)

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
            elif message.get("role") == "tool":
                msgHistory.append(
                    Content(
                        role="tool", parts=[Part.from_text(message["tool_response"])]
                    )
                )

        generation_config = GenerationConfig(
            temperature=ASSISTANT_CONFIG["LLM"]["TEMPERATURE"]
        )
        model = GenerativeModel(
            ASSISTANT_CONFIG["LLM"]["MODEL"],
            system_instruction=ASSISTANT_CONFIG["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=generation_config,
            tools=[search_tool],
        )
        streaming_model = GenerativeModel(
            ASSISTANT_CONFIG["LLM"].get(
                "STREAM_MODEL", ASSISTANT_CONFIG["LLM"]["MODEL"]
            ),
            system_instruction=ASSISTANT_CONFIG["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=GenerationConfig(
                temperature=ASSISTANT_CONFIG["LLM"]["TEMPERATURE"]
            ),
            tools=[search_tool],
        )
        prompt_template = ASSISTANT_CONFIG["LLM"]["PROMPT"]

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
        botmsg = ""

        if (estimated_token_cost / token_equivalence) > current_balance:
            botmsg = "No cuentas con suficientes tokens para realizar esta acción."
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

        @stream_with_context
        def generate_response(p):

            calls = []  # Acumularemos aquí todas las llamadas a herramientas
            usage_metadata = None
            botmsg = ""  # Initialize botmsg here

            first_stream = streaming_model.generate_content(p, stream=True)

            for chunk in first_stream:
                usage_metadata = getattr(chunk, "usage_metadata", None)

                # Check for function_call in the nested structure
                function_call = None
                if hasattr(chunk, "candidates"):
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, "content") and hasattr(
                        candidate.content, "parts"
                    ):
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call"):
                                function_call = part.function_call
                                break
                if function_call:
                    print("[DEBUG] Function call detectada:")
                    print(function_call)
                    calls.append(function_call)
                    continue  # importante: sigue iterando

                if hasattr(chunk, "text") and chunk.text:
                    print("========= Chunk ==========")
                    print(chunk.text)
                    botmsg += chunk.text
                    yield chunk.text
            print(botmsg)

            output_tokens = session_output_tokens + (
                usage_metadata.candidates_token_count if usage_metadata else 0
            )
            input_tokens = session_input_tokens + (
                usage_metadata.prompt_token_count if usage_metadata else 0
            )
            total_token_count = output_tokens + input_tokens

            print(f"[DEBUG] chatSession invocada con id: {id}")

            # Diagnóstico: ¿cuántas llamadas a herramientas hizo el modelo?
            print(f"[DEBUG] Total de llamadas a herramientas: {len(calls)}")

            # Intento estimar cuántos artículos mencionó el usuario en el mensaje
            article_matches = re.findall(
                r"(art[ií]culo(?:s)?\s+)(\d+(?:\s*(?:al|\-|\–)\s*\d+)?(?:\s*,\s*\d+)*)",
                msg.lower(),
            )
            total_detected_articles = 0

            for base, match in article_matches:
                if "al" in match or "-" in match or "–" in match:
                    # Rango: "20 al 22" o "20-22"
                    try:
                        numbers = re.findall(r"\d+", match)
                        if len(numbers) == 2:
                            start, end = map(int, numbers)
                            total_detected_articles += end - start + 1
                    except Exception as e:
                        print(
                            f"[WARN] Error procesando rango de artículos '{match}': {e}"
                        )
                else:
                    # Lista explícita: "20, 21, 22"
                    total_detected_articles += len(re.findall(r"\d+", match))

            print(
                f"[DEBUG] Artículos detectados en texto del usuario: {total_detected_articles}"
            )

            # Si el modelo llamó menos veces de lo esperado
            if total_detected_articles > 0 and len(calls) < total_detected_articles:
                print(
                    f"[ALERTA] El modelo debería haber hecho {total_detected_articles} llamadas pero solo hizo {len(calls)}."
                )

            tool_result_text = ""
            debug_log = []

            # Procesar las llamadas a herramientas en paralelo, luego se agrupan los resultados en orden
            results = []
            if len(calls) > 0:
                for i, call in enumerate(calls[0].args.get("calls")):
                    if call.get("source") == "pinecone":
                        k_val = call.get("k_count", 5)
                        results.append(
                            consultController.search(
                                query=call.get("article"),
                                id=call.get("article_id"),
                                document=call.get("document"),
                                k_count=k_val,
                            )
                        )
                    if call.get("source") == "mongo_sentencias":
                        results.append(
                            consultController.search_mongo_sentencias(
                                case_type=call.get("case_type"),
                                user_request=msg,
                            )
                        )

                msgHistory.append(
                    Content(
                        role="tool",
                        parts=[
                            Part.from_text(
                                tool_result_text + ": " + json.dumps(results)
                            )
                        ],
                    )
                )
                prompt = prompt_template.format(
                    MESSAGE="Aquí están los resultados de los artículos legales que solicitó. Redacta una respuesta clara y completa para el usuario.",
                    HISTORY=self.flatten_history(msgHistory),
                    FILE_DATA="",
                )

                second_stream = streaming_model.generate_content(prompt, stream=True)
                botmsg = ""
                for chunk in second_stream:
                    usage_metadata = getattr(chunk, "usage_metadata", None)

                    if hasattr(chunk, "text") and chunk.text:
                        botmsg += chunk.text
                        yield chunk.text

            botmsg_object = {
                "role": "model",
                "bot_response": botmsg,
                "timestamp": datetime.now(),
            }

            token_usage = total_token_count / token_equivalence
            tkbController.use_tokens(g.userId, token_usage)

            sessions.find_one_and_update(
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

        return Response(generate_response(prompt), mimetype="text/event-stream")
