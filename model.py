from sentence_transformers import SentenceTransformer

# Choose the model you want
model_name = "BAAI/bge-small-en"

# Download and cache locally
model = SentenceTransformer(model_name)

# Save the model to a local folder
model.save("models/bge-small-en")
