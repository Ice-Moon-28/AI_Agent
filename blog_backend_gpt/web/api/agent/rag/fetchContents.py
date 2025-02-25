import mmap
import os
import pickle
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datasets import load_dataset
from langchain.schema import Document
import numpy as np
from tqdm import tqdm

def fetchExampleContents():
    loader = WebBaseLoader(
        web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    return all_splits

def write_wikipedia_to_mmap(
        number=None,
        seed=42,
        mmap_file="wikipedia_mmap.dat",
        index_file="index.npy"
    ):
    """
    将 Wikipedia 数据写入 mmap 文件，并生成索引文件。
    
    :param number: 选取的文章数量（None 表示使用完整数据集）
    :param seed: 随机种子，保证可重复性
    :param mmap_file: 存储 Wikipedia 文本的 mmap 文件路径
    :param index_file: 存储索引数据的文件路径
    """

    dataset = load_dataset("wikipedia", "20220301.en", trust_remote_code=True)
    
    print("The length of dataset is: ", len(dataset['train']))

    if os.path.exists(mmap_file) and os.path.exists(index_file):
        print(f"文件 {mmap_file} 和 {index_file} 已存在，跳过写入。")
        return

    if number is not None:
        sampled_data = dataset['train'].shuffle(seed=seed).select(range(number))
    else:
        sampled_data = dataset['train']

    with open(mmap_file, "wb") as f:
        indices = []  
        offset = 0

        for entry in tqdm(sampled_data, desc="Writing to mmap", unit="doc"):
            try:
                text = entry["text"]
                data = pickle.dumps(text) 
                f.write(data)  
                indices.append(offset)  
                offset += len(data)  
            except Exception as e:
                print(f"❌ Error: {e} \n Entry: {entry}")

    np.save(index_file, np.array(indices)) 
    print(f"✅ 数据已写入 mmap 文件: {mmap_file}")
    print(f"✅ 索引已存储: {index_file}")

def read_wikipedia_from_mmap(
        mmap_file="wikipedia_mmap.dat",
        index_file="index.npy",
        chunk_size=512,
        chunk_overlap=100
    ):
    """
    从 mmap 文件读取 Wikipedia 文本，并按块拆分后逐步返回。

    :param mmap_file: 存储 Wikipedia 文本的 mmap 文件路径
    :param index_file: 存储索引数据的文件路径
    :param chunk_size: 文本拆分块的大小
    :param chunk_overlap: 拆分块之间的重叠字符数
    :yield: 逐条返回拆分后的文本块
    """
    # 2️⃣ **读取 mmap 文件**
    with open(mmap_file, "r+b") as f, open(index_file, "rb") as index_f:
        mmapped_data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        indices = np.load(index_f)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        for i in range(len(indices)):
            start = indices[i]
            end = indices[i + 1] if i + 1 < len(indices) else len(mmapped_data)
            try:
                text = pickle.loads(mmapped_data[start:end])  # 读取 & 反序列化文本
                if text.strip():
                    doc = Document(page_content=text)
                    yield from text_splitter.split_documents([doc])  # **流式处理**
            except Exception as e:
                print("Error loading document:", e)

def fetchWikipediaContents_memmap(
        number=None,
        seed=42,
        memmap_file="wikipedia_memmap.dat",
        max_entries=100000,  # 设定最大条目数，防止 memmap 文件过大
        chunk_size=512,
        chunk_overlap=100
    ):
    dataset = load_dataset("wikipedia", "20220301.en")

    print("The length of dataset is: ", len(dataset['train']))

    if number is not None:
        sampled_data = dataset['train'].shuffle(seed=seed).select(range(number))
    else:
        sampled_data = dataset['train']

    max_text_length = 2000
    dtype = f'U{max_text_length}'  

    memmap_shape = (min(max_entries, len(sampled_data)),)
    memmap_data = np.memmap(memmap_file, dtype=dtype, mode='w+', shape=memmap_shape)

    for i, entry in enumerate(sampled_data):
        if i >= max_entries:
            break 
        try:
            memmap_data[i] = entry["text"][:max_text_length]  
        except Exception as e:
            print(e, entry)
    
    memmap_data.flush()

    del memmap_data  

    memmap_data = np.memmap(memmap_file, dtype=dtype, mode='r', shape=memmap_shape)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for text in memmap_data:
        if text.strip(): 
            doc = Document(page_content=text)
            yield from text_splitter.split_documents([doc]) 