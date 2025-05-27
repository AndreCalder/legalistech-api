import os
from pinecone.grpc import PineconeGRPC as Pinecone
import re


def get_numeric_id(item):
    match = re.search(r"\d+", item["id"])
    return int(match.group()) if match else 0


class ConsultController:

    def search(self, query, document=None):

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
            filter_query = {"metadata.documento":{"$eq": document}}

        results = index.query(
            namespace="milegalista",
            vector=query_embedding[0].values,
            top_k=15,
            include_values=False,
            include_metadata=True,
            filter=filter_query,
        )

        result_arr = []

        results.matches.sort(key=lambda x: x.get("score", 0), reverse=True)

        for match in results.matches:
            if match.get("score") > 0.79:
                result_arr.append(
                    {"id": match.get("id"), "metadata": match.get("metadata")}
                )

        return result_arr, 200

    
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