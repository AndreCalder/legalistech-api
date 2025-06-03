import os
from pinecone.grpc import PineconeGRPC as Pinecone
import re
import unicodedata
from controllers.util.mongo_assistant_config import MONGO_ASSISTANT_CONFIG
from mongoConnection import db
from bson import ObjectId
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Content,
    Part,
)
from bson import json_util


sentencias = db["sentencias"]


def decodify(raw_text):

    cases = []

    for block in raw_text.split("#CASE"):
        if not block.strip():
            continue
        case = {}
        case["type"] = re.search(r"TYPE:\s*(.+)", block).group(1)
        case["resolution"] = re.search(r"RESOLUTION:\s*(.+)", block).group(1)
        case["outcome"] = re.search(r"OUTCOME:\s*(.+)", block).group(1)
        case["reasons"] = re.search(r"REASONS:\s*(.+)", block).group(1).split(")")
        case["laws"] = re.findall(r"([A-Z]+):([\d\w]+)", block)
        cases.append(case)
        
    return cases


def get_numeric_id(item):
    match = re.search(r"\d+", item["id"])
    return int(match.group()) if match else 0


class ConsultController:

    def __init__(self):
        self.sentencias = db["sentencias"]

    def search_mongo_sentencias(self, case_type, user_request):

        print(case_type)
        print(user_request.get("file_data"))
        found_sentencias = sentencias.find(
            {
                "case_info.case_type": case_type,
            },
            {
                "_id": 0,
                "case_info.court": 0,
                "case_info.court": 0,
                "case_info.date_resolved": 0,
                "case_info.date_filed": 0,
            },
        )

        formatted_sentencias = json_util.loads(json_util.dumps(found_sentencias))

        model_cfg = MONGO_ASSISTANT_CONFIG

        generation_config = GenerationConfig(
            temperature=MONGO_ASSISTANT_CONFIG["LLM"]["TEMPERATURE"]
        )

        model = GenerativeModel(
            model_cfg["LLM"]["MODEL"],
            system_instruction=model_cfg["LLM"]["SYSTEM_INSTRUCTION"],
            generation_config=generation_config,
        )

        prompt_template = model_cfg["LLM"]["PROMPT"]
        prompt = prompt_template.format(
            MESSAGE=user_request.get("user_question"),
            FILE_DATA=user_request.get("file_data"),
            SENTENCES=formatted_sentencias,
        )
        
        print(prompt)

        response = model.generate_content(prompt)

        return response.text

    def normalize_string(self, text: str) -> str:
        # Remove accents (é → e, ñ → n, etc.)
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ASCII", "ignore")
            .decode("utf-8")
        )

        # Remove all non-alphanumeric characters (except spaces)
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

        # Optional: remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def search(self, query, id=None, document=None, k_count=5):

        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("milegalista")
        query_embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[f"query: {query}"],
            parameters={"input_type": "query"},
        )

        # Optional document filtering
        filter_query = {}
        if document:
            filter_query["documento"] = {"$eq": self.normalize_string(document)}

        results = index.query(
            namespace="milegalista",
            vector=query_embedding[0].values,
            top_k=k_count,
            include_values=False,
            include_metadata=True,
            filter=filter_query,
        )
        result_arr = []

        results.matches.sort(key=lambda x: x.get("score", 0), reverse=True)

        print(results)
        print(id)
        if id:
            results.matches = [
                match for match in results.matches if match.get("id") == id
            ]

        for match in results.matches:
            if match.get("score") > 0.7:
                result_arr.append(
                    {"id": match.get("id"), "metadata": match.get("metadata")}
                )

        return result_arr

    # Create get by ID method, return only one result.

    def get_by_id(self, document_id):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("milegalista")

        try:
            results = index.fetch(ids=[document_id], namespace="milegalista")
            match = results.vectors.get(document_id)
            if match:
                return {
                    "id": match.get("id"),
                    "metadata": match.get("metadata"),
                }, 200
            else:
                return {"error": "Document not found"}, 404

        except Exception as e:
            return {"error": str(e)}, 500
