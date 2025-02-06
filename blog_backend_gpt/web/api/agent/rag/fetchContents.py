import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datasets import load_dataset
from langchain.schema import Document

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

def fetchWikipediaContents(number=5000):
    dataset = load_dataset("wikipedia", "20220301.en")

    docs = []

    sampled_data = dataset['train'].shuffle(seed=42).select(range(number))

    for entry in sampled_data:
        try:
            docs.append(Document(page_content=entry["text"]))
        except Exception as e:
            print(e, entry)

    # 进行文本拆分
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    return all_splits

