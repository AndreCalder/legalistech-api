import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="mlai-434520", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-001")
response = model.generate_content("Hello, world!")