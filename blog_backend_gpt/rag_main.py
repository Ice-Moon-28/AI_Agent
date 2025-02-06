from blog_backend_gpt.web.api.agent.rag.fetchContents import  fetchExampleContents, fetchWikipediaContents
from blog_backend_gpt.web.api.agent.rag.vectorStore import add_vector_content_parallel, create_vector_store, add_vector_content, faiss_save_vector_store, init_mongodb


def rag_main():

    # init_mongodb()

    content = fetchWikipediaContents(10000)

    print("get the content of examples the length of passage is", len(content))

    # vector_store = create_vector_store(type='faiss')

    print("Init the vector store", len(content))

    add_vector_content_parallel(
        documents=content,
        batch_size=500,
        num_workers=4,
    )

    # faiss_save_vector_store(vector_store, "test.bin")

    print("Add content to the vector store", len(content))

if __name__ == "__main__":
    rag_main()