from vertexai.preview.generative_models import FunctionDeclaration, Tool

# Función combinada que permite búsquedas en Pinecone (artículos/leyes) o MongoDB (jurisprudencia).
combined_search = FunctionDeclaration(
    name="combined_legal_search",
    description=(
        "Realiza una búsqueda en Pinecone (búsqueda semántica de artículos/leyes) "
        "o en MongoDB ('sentencias') dependiendo de la intención del usuario. "
        "Usa 'pinecone' para artículos legales y leyes, y 'mongo_sentencias' para jurisprudencia."
    ),
    parameters={
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["pinecone", "mongo_sentencias"],
                "description": (
                    "Indica el origen de la búsqueda: 'pinecone' para leyes o artículos, "
                    "'mongo_sentencias' para jurisprudencia."
                ),
            },
            "document": {
                "type": "string",
                "description": "Nombre o fragmento del documento legal (por ejemplo, 'Código Civil').",
            },
            "case_type": {
                "type": "string",
                "description": (
                    "Obligatorio si source es 'mongo_sentencias'. Tipo de caso: "
                    "'Controversias Familiares', 'Divorcios', etc."
                ),
            },
            "subject": {
                "type": "string",
                "description": "Consulta en lenguaje natural o tema general.",
            },
            "article_id": {
                "type": "string",
                "description": "ID del artículo (por ejemplo, 'cc_articulo_123').",
            },
            "article": {
                "type": "string",
                "description": "Nombre legible del artículo (por ejemplo, 'artículo 123').",
            },
            "k_count": {
                "type": "integer",
                "description": (
                    "Número de resultados relevantes a devolver. "
                    "Usualmente 5 para artículos y 50 para sentencias judiciales."
                ),
            },
        },
        "required": ["source", "k_count"],
    },
)

# Función para limpiar historial de la sesión actual.
clear_history = FunctionDeclaration(
    name="reset_session_history",
    description="Borra el historial de la sesión actual si el usuario lo solicita explícitamente.",
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "ID de sesión (ObjectId de MongoDB, string hexadecimal de 24 caracteres).",
            }
        },
        "required": ["session_id"],
    },
)

# Herramienta principal expuesta a Gemini, incluye búsqueda legal y limpieza de sesión
search_tool = Tool.from_function_declarations([combined_search, clear_history])
