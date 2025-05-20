import os
from pinecone.grpc import PineconeGRPC as Pinecone
import re


def get_numeric_id(item):
    match = re.search(r"\d+", item["id"])
    return int(match.group()) if match else 0


class ConsultController:

    def search(self, query):

        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("milegalista")

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

        results.matches.sort(key=lambda x: x.get("score", 0), reverse=True)

        for match in results.matches:
            if match.get("score") > 0.79:
                result_arr.append(
                    {"id": match.get("id"), "metadata": match.get("metadata")}
                )

        return result_arr, 200
