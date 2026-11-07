# Run from the project root:  python -m rag.test_embeddings
from rag.embeddings import generate_embedding

text = "What is the punishment for theft?"

vector = generate_embedding(text)

print("Vector dimensions:", len(vector))
print("First five values:", vector[:5])