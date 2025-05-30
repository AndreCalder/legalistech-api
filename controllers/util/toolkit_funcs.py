from vertexai.generative_models import FunctionDeclaration, Tool

process_pdf = FunctionDeclaration(
    name="process_pdf_document",
    description="Process a PDF document and extract the text content to be used in the LLM model.",
    parameters={
        "type": "object",
        "properties": {},
    },
)

process_pdf_tool = Tool(
    function_declarations=[process_pdf],
)

pinecone_consult = FunctionDeclaration(
    name="pinecone_consult",
    description=(
        "Search for legal documents in the Pinecone database using natural language queries in Spanish. "
    ),
    parameters={
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "Optional. The query to search for legal documents in the Pinecone database, could be context, specific legal topic or question",
            },
            "document": {
                "type": "string",
                "description": (
                    "Optional. The specific document to search in. If not provided, "
                    "the search will be performed across all documents."
                ),
            },
            "article_id": {
                "type": "string",
                "description": (
                    "Optional. The specific article to search in. If not provided, "
                    "the search will be performed across all articles. "
                    "For example: 'cc_articulo_123' for Código Nacional de Procedimientos Civiles y Familiares."
                ),
            },
            "article": {
                "type": "string",
                "description": (
                    "Optional. The specific article to search in. If not provided, "
                    "the search will be performed across all articles. for example: 'artículo 123'. "
                ),
            },
            "k_count": {
                "type": "integer",
                "description": (
                    "The number of top results to return. Defaults to 5 if not provided."
                    " If a specific law or article is provided set it to 1, otherwise come up with a reasonable number of results to return."
                ),
            },
        },
        "required": ["k_count"],
    },
)

pinecone_consult_tool = Tool(function_declarations=[pinecone_consult])

mongo_sentencias_consult = FunctionDeclaration(
    name="mongo_sentencias_consult",
    description="Consulta documentos en la colección 'sentencias' de MongoDB.",
    parameters={
        "type": "object",
        "properties": {
            "sentencia_id": {
                "type": "string",
                "description": "ID de la sentencia (ObjectId como string)."
            },
            "document": {
                "type": "string",
                "description": "Nombre o fragmento del archivo (campo file_name)."
            },
            "article_id": {
                "type": "string",
                "description": "Artículo específico o ID a buscar dentro del texto del documento."
            },
            "article": {
                "type": "string",
                "description": "Artículo en lenguaje natural, como 'artículo 123'."
            },
            "k_count": {
                "type": "integer",
                "description": "Número máximo de resultados (default 5)."
            }
        },
        "required": ["k_count"]
    }
)

mongo_sentencias_tool = Tool(function_declarations=[mongo_sentencias_consult])
