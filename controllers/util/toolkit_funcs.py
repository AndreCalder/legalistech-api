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
        "Search the legal vector database in Spanish for constitutional articles, laws, or jurisprudence relevant to the user's request. "
        "Use this tool when additional legal context may help clarify or support your response. "
        "Generate one or more well-formed legal queries in Spanish, based on the arguments found in the user's message or uploaded document."
    ),
    parameters={
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "A natural language legal query written in Spanish, focused on a specific argument or legal concern.",
                },
                "description": "An array of legal search queries in Spanish, each one addressing a distinct argument or legal issue.",
            }
        },
        "required": [],
    },
)

pinecone_consult_tool = Tool(function_declarations=[pinecone_consult])
