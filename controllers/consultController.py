# Change Log
# - Implemented ConsultController for handling legal document searches and retrievals.
# === Andre - Moved import statements to the top for better organization & performance.

import os
import re
import unicodedata
from datetime import datetime
from bson import ObjectId, json_util
from pinecone.grpc import PineconeGRPC as Pinecone
from mongoConnection import db
from controllers.util.mongo_assistant_config import MONGO_ASSISTANT_CONFIG
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, GenerationConfig

# 📚 Colección de sentencias judiciales
sentencias = db["sentencias"]
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("milegalista")


class ConsultController:
    def __init__(self):
        self.sentencias = sentencias

    def normalize_string(self, text: str) -> str:
        """
        Normaliza una cadena para eliminar acentos y símbolos especiales.
        Utilizado para construir filtros de búsqueda más robustos.
        """
        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def search(self, query, id=None, document=None, k_count=5):
        """
        Realiza una búsqueda en Pinecone. Si k_count == 1 y se proporciona un ID,
        intenta obtener el documento exacto vía fetch(). De lo contrario,
        ejecuta búsqueda semántica por vector.
        """


        # 🎯 Si k_count = 1 y hay ID, intentamos obtener solo ese artículo directamente
        if k_count == 1 and id:
            print(f"[DEBUG] Realizando búsqueda directa por ID debido a k_count = 1")
            exact, status = self.get_by_id(id)
            if status == 200:
                return {"exact_match": exact, "similar_matches": []}
            else:
                print(f"[DEBUG] No se encontró el artículo exacto con ID: {id}")
                return {"exact_match": None, "similar_matches": []}

        # ✨ Búsqueda vectorial semántica
        embed_input = f"{query} en el contexto de {document}" if document and query else query or document
        print(f"[DEBUG] PINECONE_EMBED INPUT → '{embed_input}'")

        query_embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[embed_input],
            parameters={"input_type": "query"},
        )

        filter_query = {}
        if document:
            norm_doc = self.normalize_string(document)
            print(f"[DEBUG] Normalized document: '{norm_doc}'")
            if norm_doc:
                filter_query["documento"] = {"$eq": norm_doc}

        results = index.query(
            namespace="milegalista",
            vector=query_embedding[0].values,
            top_k=k_count,
            include_values=False,
            include_metadata=True,
            filter=filter_query,
        )

        print(f"[DEBUG] Returned {len(results.matches)} raw matches")

        exact_match = None
        similar_matches = []

        for i, match in enumerate(results.matches):
            match_id = match.get("id")
            score = match.get("score", 0)
            metadata = match.get("metadata", {})

            print(f"\n[DEBUG] RAW MATCH {i+1}")
            print(f"ID: {match_id}")
            print(f"SCORE: {score}")
            print(f"DOCUMENTO: {metadata.get('documento')}")
            print(f"TEXTO: {metadata.get('texto', '')[:300]}...")

            result_obj = {
                "id": match_id,
                "score": score,
                "metadata": metadata,
            }

            # Si coincide exactamente con el ID proporcionado
            if id and match_id == id:
                exact_match = result_obj
                print(f"[DEBUG] ✅ ID exacto '{id}' encontrado entre los matches.")

            if score > 0.7 and match_id != id:
                similar_matches.append(result_obj)

        if id and not exact_match:
            print(f"[DEBUG] ⚠️ No se encontró el artículo exacto '{id}' en los resultados relevantes.")

        if not exact_match and not similar_matches:
            print("[DEBUG] No matches exceeded the threshold (> 0.7)")

        return {
            "exact_match": exact_match,
            "similar_matches": similar_matches
        }

    def search_mongo_sentencias(self, case_type, user_request):
        """
        Recupera sentencias del tipo solicitado desde MongoDB y
        genera una respuesta contextual con Vertex AI.
        """
        mongo_query = {"case_info.case_type": case_type}
        projection = {
            "case_info.court": 0,
            "case_info.date_resolved": 0,
            "case_info.date_filed": 0,
        }

        found = list(self.sentencias.find(mongo_query, projection))
        print(f"[DEBUG] Found {len(found)} sentencias for case_type '{case_type}'")

        for s in found:
            s.pop("_id", None)

        model_cfg = MONGO_ASSISTANT_CONFIG
        generation_config = GenerationConfig(temperature=model_cfg["LLM"]["TEMPERATURE"])
        model = GenerativeModel(
            model_cfg["LLM"]["MODEL"],
            system_instruction=model_cfg["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=generation_config,
        )

        prompt = model_cfg["LLM"]["PROMPT"].format(
            MESSAGE=user_request.get("user_question"),
            FILE_DATA=user_request.get("file_data"),
            SENTENCES=json_util.loads(json_util.dumps(found)),
        )

        response = model.generate_content(prompt)
        return response.text

    def get_by_id(self, document_id):
        """
        Recupera un artículo exacto desde Pinecone usando su ID directo.
        Usado para truncar búsquedas cuando solo se pide un artículo.
        """
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("milegalista")

        try:
            results = index.fetch(ids=[document_id], namespace="milegalista")
            match = results.vectors.get(document_id)
            if match:
                print(f"[DEBUG] Documento encontrado por ID '{document_id}'.")
                return {
                    "id": match.get("id"),
                    "metadata": match.get("metadata"),
                }, 200
            print(f"[DEBUG] Documento no encontrado por ID '{document_id}'.")
            return {"error": "Document not found"}, 404
        except Exception as e:
            print(f"[DEBUG] Error al buscar por ID '{document_id}': {str(e)}")
            return {"error": str(e)}, 500
