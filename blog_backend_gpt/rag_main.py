from blog_backend_gpt.web.api.agent.rag.fetchContents import write_wikipedia_to_mmap
from blog_backend_gpt.web.api.agent.rag.vectorStore import create_vector_store, add_vector_content
from datasets import load_dataset


def rag_main():

    # init_mongodb()

    try:

        # print("get the content of examples the length of passage is", len(content))

        vector_store = create_vector_store(type='faiss', embedding_type="all-mpnet-base-v2")

        print("Init the vector store")

        write_wikipedia_to_mmap()

        # add_vector_content(vector_store, content, batch_size=256)

    except Exception as e:
        print(e)

    # faiss_save_vector_store(vector_store, "test.bin")

    # print("Add content to the vector store", len(content))

    # documents = get_related_documents(vector_store, "Movie")

    # print(documents)


if __name__ == "__main__":
    rag_main()