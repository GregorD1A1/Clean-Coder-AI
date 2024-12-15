import os
import cohere
import chromadb
from pathlib import Path
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
cohere_key = os.getenv("COHERE_API_KEY")
if cohere_key:
    cohere_client = cohere.Client(cohere_key)
collection_name = f"clean_coder_{Path(work_dir).name}_file_descriptions"


def get_collection():
    if cohere_key:
        chroma_client = chromadb.PersistentClient(path=os.getenv('WORK_DIR') + '/.clean_coder/chroma_base')
        try:
            return chroma_client.get_collection(name=collection_name)
        except ValueError:
            print("Vector database does not exist. (Optional) create it by running src/tools/rag/write_descriptions.py to improve file research capabilities")
            return False
    return False


collection = get_collection()


def vdb_available():
    return True if get_collection() else False


def retrieve(question):
    retrieval = collection.query(query_texts=[question], n_results=8)
    reranked_docs = cohere_client.rerank(
        query=question,
        documents=retrieval["documents"][0],
        top_n=4,
        model="rerank-english-v3.0",
        #return_documents=True,
    )
    reranked_indexes = [result.index for result in reranked_docs.results]
    response = ""
    for index in reranked_indexes:
        filename = retrieval["ids"][0][index]
        description = retrieval["documents"][0][index]
        response += f"{filename}:\n\n{description}\n\n"
    response += "\n\nRemember to see files before adding to final response!"

    return response

if __name__ == "__main__":
    question = "Common styles, used in the main page"
    results = retrieve(question)
    print("\n\n")
    print("results: ", results)
