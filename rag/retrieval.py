import os
import cohere
import chromadb
from pathlib import Path
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")

chroma_client = chromadb.PersistentClient(path=os.getenv('WORK_DIR') + '.clean_coder/chroma_base')
collection_name = f"clean_coder_{Path(work_dir).name}_file_descriptions"
collection = chroma_client.get_collection(name=collection_name)

cohere_client = cohere.Client(os.getenv("YOUR_COHERE_API_KEY"))


def retrieve(question):
    retrieval = collection.query(query_texts=[question], n_results=8)
    print("retrieval: ", retrieval)

    reranked_docs = cohere_client.rerank(
        query=question,
        documents=retrieval["documents"][0],
        top_n=4,
        model="rerank-english-v3.0",
        #return_documents=True,
    )
    print("reranked_docs: ", reranked_docs)
    reranked_indexes = [result.index for result in reranked_docs.results]
    response = ""
    for index in reranked_indexes:
        filename = retrieval["ids"][0][index]
        description = retrieval["documents"][0][index]
        response += f"{filename}:\n\n{description}\n\n"
    response += "\n\nRemember to see files before adding to final response!"

    return response

if __name__ == "__main__":
    question = "Place where client can register"
    results = retrieve(question)
    print("results: ", results)
