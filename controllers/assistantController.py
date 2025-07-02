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
from mongoConnection import db
from controllers.util.gcp_cloudvision import scan_pdf_to_text
from controllers.util.toolkit_funcs import search_tool, clear_history
from controllers.util.assistant_config import ASSISTANT_CONFIG
from controllers.util.mongo_assistant_config import MONGO_ASSISTANT_CONFIG
from controllers.eventController import EventController
from controllers.token_balance_controller import Token_Balance_Controller
from controllers.consultController import ConsultController
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        history = session.get("history", [])
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

            function_call = None

            first_stream = model.generate_content(p, stream=True)

            function_call = None
            usage_metadata = None
            
            # Iterar sobre los chunks del stream
            for chunk in first_stream:
               
                usage_metadata = getattr(chunk, "usage_metadata", None)
                # Check if the chunk has a function call
                if getattr(chunk, "function_call", None):
                    print(chunk.function_call)
                    function_call = chunk.function_call
                    break
                
                print("========= Chunk ==========")
                yield chunk.text

            print(function_call)
            output_tokens = (
                session.get("output_tokens", 0) + usage_metadata.candidates_token_count
            )
            input_tokens = (
                session.get("input_tokens", 0) + usage_metadata.prompt_token_count
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
        
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.process_call, i, call)
                    for i, call in enumerate(calls)
                ]
                results = [None] * len(futures)
                for future in as_completed(futures):
                    i, result_text, log = future.result()
                    results[i] = (result_text, log)

            for result_text, log in results:
                tool_result_text += result_text
                debug_log.append(log)

            msgHistory.append(
                Content(
                    role="tool",
                    parts=[
                        Part.from_text(
                            tool_result_text + "\n[DEBUG] " + "; ".join(debug_log)
                        )
                    ],
                )
            )
            prompt = prompt_template.format(
                MESSAGE="Aquí están los resultados de los artículos legales que solicitó. Redacta una respuesta clara y completa para el usuario.",
                HISTORY=self.flatten_history(msgHistory),
                FILE_DATA="",
            )
            response = model.generate_content(prompt)

            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                # Esto previene errores cuando la respuesta incluye una llamada a herramienta (function_call) en lugar de texto
                botmsg = ""
                for part in parts:
                    # Si el part es un diccionario con texto (estructura JSON)
                    if isinstance(part, dict) and "text" in part:
                        botmsg += part["text"]
                    # Si el part es un objeto con atributo .text
                    elif hasattr(part, "text"):
                        botmsg += part.text
                    # Si no contiene texto (ej. function_call), se ignora para evitar errores
            else:
                botmsg = "Respuesta generada por herramienta."

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

        return Response(generate_response(prompt), mimetype="text/event-stream")
