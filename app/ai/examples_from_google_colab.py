import openai
from google.colab import userdata
import google.generativeai as genai

# API keys
openai_api_key = userdata.get('OPENAI_API_KEY')
# google_api_key = userdata.get('GOOGLE_API_KEY')

openai.api_key = openai_api_key
# genai.configure(api_key=google_api_key)

# Initialize Gemini model
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def generate_feedback(problem, level, problem_type, spk, sal, sa, feedback_type,
                      llm_model="gpt-4o", collection_name="combined_data_chunks"):
    """
    Generate feedback using RAG + CoT prompt.
    """

    # Create embedding for problem context
    query_text = f"{problem} {sa}"
    query_embedding = embedding_model.encode(query_text).tolist()

    # Search in Qdrant
    search_result = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=3,
        with_payload=True
    )

    if not search_result or not search_result.points:
        relevant_text = "No relevant context found."
    else:
        relevant_text = "\n".join([p.payload.get("text","") for p in search_result.points])

    # Construct CoT prompt
    cot_prompt = f"""
#Explain task
Generate feedback for junior high school students who are going to solve algebra problems.
Given information as follows:

[Information about current problem]
Problem: {problem}
Level: {level}
Type: {problem_type}

[Student Information]
Student Prior Knowledge: {spk}
Student Achievement Level: {sal}
Student Current Answer: {sa}

[Feedback given]
Feedback Type: {feedback_type}

[Relevant information about knowledge]
{relevant_text}

You should follow these steps:
1. Understand the problem and student information carefully.
2. Identify the student error.
3. Based on information related to current problem, information, and feedback type should be given, generate the feedback in bahasa Indonesia.
4. DO NOT give solution directly.
5. Return the feedback in JSON format as follow:
   Feedback Type:'', Feedback:''
6. The feedback SHOULD BE in Indonesian.
7. The feedback should be student friendly, you must act as peer tutor.
8. Write the math expression in latex format which starts and end with '$' 

Description about feedback:
Response-contingent is detailed comments that highlight the learner's particular response. It might explain why the right response is right and the incorrect one is incorrect. No formal error analysis is used here.
Topic-contingent is detailed feedback that gives the student details about the subject they are currently studying. This could just
mean reteaching the content.
Correct response is informs the student of the correct answer to the problem solved with no additional information.
Verification informs the students about the correctness of their response(s), such as right/wrong or overall percentage correct.
Try-again informs the student if they made an incorrect response and allows the student one or more attempts to answer the questions.

"""

    # Call selected LLM
    try:
        if llm_model == "gpt-4o":
            response = openai.chat.completions.create(
                model=llm_model,  
                messages=[
                    {"role": "system", "content": "You are an expert math tutor."},
                    {"role": "user", "content": cot_prompt}
                ],
                max_tokens=1000
            )
            print("\n===== MODEL OUTPUT =====")
            print(response.choices[0].message.content)
            
            # ✅ Extract token usage
            print("\n--- TOKEN USAGE ---")
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Completion tokens: {response.usage.completion_tokens}")
            print(f"Total tokens: {response.usage.total_tokens}")

            return response.choices[0].message.content
        elif llm_model == "gpt-5-nano" or llm_model == "gpt-5-mini" or llm_model =="gpt-5":
            response = openai.chat.completions.create(
                model=llm_model,  
                messages=[
                    {"role": "system", "content": "You are an expert math tutor."},
                    {"role": "user", "content": cot_prompt}
                ],
                max_completion_tokens=1000,
                temperature=0.2
            )
            print("\n===== MODEL OUTPUT =====")
            print(response.choices[0].message.content)

            # ✅ Extract token usage
            print("\n--- TOKEN USAGE ---")
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Completion tokens: {response.usage.completion_tokens}")
            print(f"Total tokens: {response.usage.total_tokens}")

            return response.choices[0].message.content
        elif llm_model == "gemini":
            response = gemini_model.generate_content(cot_prompt)
            return response.text

        else:
            return "❌ Invalid model. Choose: 'gpt-4o', 'gpt-5', or 'gemini'."

    except Exception as e:
        return f"⚠️ LLM Error: {e}"

import numpy as np
import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Filepaths where embeddings and chunks are saved
embeddings_file = "30-31 Oktober_chunk_embeddings.npy"
chunks_file = "chunks.json"

# Load embeddings
try:
    chunk_embeddings = np.load(embeddings_file)
    print(f"✅ Loaded embeddings from {embeddings_file}")
except FileNotFoundError:
    print(f"Error: {embeddings_file} not found. Please ensure embeddings are generated and saved.")
    raise

# Load chunks
try:
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"✅ Loaded chunks from {chunks_file}")
except FileNotFoundError:
    print(f"Error: {chunks_file} not found. Please ensure chunks are generated and saved.")
    raise

# Initialize Qdrant client
# Using an in-memory instance for this example, but you can configure a persistent one
client = QdrantClient(":memory:")

# Define vector parameters
# The size should match the output dimension of your embedding model
# Assuming chunk_embeddings is a 2D array (num_chunks, embedding_dim)
vector_params = VectorParams(size=chunk_embeddings.shape[1], distance=Distance.COSINE)

# Create a collection
collection_name = "combined_data_chunks"
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=vector_params,
)

# Prepare data for upsert
points = [
    PointStruct(id=i, vector=chunk_embeddings[i].tolist(), payload={"text": chunks[i]})
    for i in range(len(chunks))
]

# Upsert data to the collection
client.upsert(
    collection_name=collection_name,
    wait=True,
    points=points
)

print(f"Stored {len(points)} points in Qdrant collection '{collection_name}'.")
