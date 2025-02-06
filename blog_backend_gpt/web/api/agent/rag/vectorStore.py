

from multiprocessing import Pool
from typing import List
from uuid import uuid4

from tqdm import tqdm
from blog_backend_gpt.web.api.agent.rag.embeddingText import get_embedding_text
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient


def init_mongodb():
    """
    连接 MongoDB 并初始化数据库 backend_gpt 和集合 document
    """

    client = MongoClient("mongodb://root:agent_backend@localhost:27000/admin")

    db = client["backend_gpt"]

    collection = db["document"]

    # 确保数据库和集合存在
    if collection.count_documents({}) == 0:
        documents = [
            {"title": "Hello GPT", "content": "This is a test document.", "author": "User"},
            {"title": "MongoDB Guide", "content": "MongoDB collections do not require predefined schemas.", "author": "Admin"}
        ]
        collection.insert_many(documents)
        print("✅ Inserted initial data into `backend_gpt.document`.")

    print("✅ MongoDB database `backend_gpt` initialized.")
    
    # 关闭连接
    client.close()

def create_mongdb_client():
    mongo_client = MongoClient("mongodb://root:agent_backend@localhost:27000/")
    db = mongo_client["backend_gpt"]  
    collection = db["document"] 
    return collection



def create_mongdb_vector_store():
    import os
    os.environ["OLLAMA_ACCELERATOR"] = "metal"
    embedding = get_embedding_text("ollama3")

    db_collection = create_mongdb_client()

    vector_store = MongoDBAtlasVectorSearch(
        embedding=embedding,
        collection=db_collection,
        index_name="vector_index",
        relevance_score_fn="cosine",
    )

    return vector_store




import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS


def create_faiss_vector_store():
    import os
    os.environ["OLLAMA_ACCELERATOR"] = "metal"
    embeddings = get_embedding_text("ollama3")
    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))

    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    return vector_store

def create_vector_store(type: str='mongdb'):
    if type == "faiss":
        return create_faiss_vector_store()

    if type == "mongdb":
        return create_mongdb_vector_store()
    
    return None

def get_related_documents(
        vector_store,
        query: str
    ):
    return vector_store.similarity_search(query, k=3)

def insert_vectors(content_batch, type):
    vector_store = create_vector_store(type)  # 每个进程单独创建 vector_store
    vector_store.add_documents(content_batch)  # 插入数据
    return f"Inserted {len(content_batch)} documents"

def add_vector_content(vector_store, documents, batch_size=20):

    num_batches = len(documents) // batch_size + (1 if len(documents) % batch_size != 0 else 0)

    for i in tqdm(range(num_batches), desc="Adding Documents"):
        batch = documents[i * batch_size : (i + 1) * batch_size]
        ids = [uuid4().hex for _ in range(len(batch))]
        vector_store.add_documents(batch, ids=ids) 
    
    print("✅ 向量内容插入完成！")

from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from uuid import uuid4

def add_documents_batch(args):
    """ 子进程执行的批量插入任务 """
    vector_store = create_vector_store(type='faiss')
    id, batch = args
    ids = [uuid4().hex for _ in batch]
    vector_store.add_documents(batch, ids=ids) 
    vector_store.save_local(f"test{id}.bin")
    return len(batch)  

def add_vector_content_parallel(documents, batch_size=20, num_workers=None):
    """ 使用多进程池并行插入向量数据 """
    if num_workers is None:
        num_workers = min(4, cpu_count())  # 限制最大进程数，防止过载

    num_batches = len(documents) // batch_size + (1 if len(documents) % batch_size != 0 else 0)
    batches = [(i, documents[i * batch_size : (i + 1) * batch_size]) for i in range(num_batches)]
    
    with Pool(processes=num_workers) as pool:
        for _ in tqdm(pool.imap_unordered(add_documents_batch, batches),
                      total=num_batches, desc="Adding Documents (Multiprocessing)"):
            pass

    print("✅ 向量内容插入完成！")

def faiss_save_vector_store(vector_store, file_path):
    vector_store.save_local(file_path)

    print("✅ 向量内容保存完成！", file_path)

def faiss_load_vector_store(file_path):
    print("✅ 向量内容加载完成！", file_path)

    return FAISS.load_local(file_path)

