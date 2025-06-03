from vertexai.preview.generative_models import FunctionDeclaration, Tool

combined_search = FunctionDeclaration(
    name="combined_legal_search",
    description=(
        "Perform a search in either Pinecone (semantic search for articles/laws) or MongoDB ('sentencias') "
        "depending on the query intent. Use 'pinecone' for legal articles or laws, and 'mongo_sentencias' for case law tips."
    ),
    parameters={
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["pinecone", "mongo_sentencias"],
                "description": "Choose which backend to query: 'pinecone' for law/article queries, 'mongo_sentencias' for case law research.",
            },
            "document": {
                "type": "string",
                "description": "Name or fragment of the document (e.g. 'Código Civil').",
            },
            "case_type": {
                "type": "string",
                "description": (
                    "Required if source is 'mongo_sentencias'. Type of case like 'Controversias Familiares', 'Divorcios', etc."
                ),
            },
            "subject": {
                "type": "string",
                "description": "Free-text query or topic.",
            },
            "article_id": {
                "type": "string",
                "description": "Article ID (e.g. 'cc_articulo_123').",
            },
            "article": {
                "type": "string",
                "description": "Human-friendly article name (e.g. 'artículo 123').",
            },
            "k_count": {
                "type": "integer",
                "description": "Number of top results to return (5 for articles, 50 for case law).",
            },
        },
        "required": ["source", "k_count"],
    },
)

search_tool = Tool.from_function_declarations([combined_search])
