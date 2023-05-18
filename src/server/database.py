import pinecone
import os
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from typing import Optional
from logger import logger


PINECONE_API_KEY = os.environ.get("PINECODE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


class vectordb:
    def __init__(self, number_of_retrieval_results: Optional[int]):
        # Validation
        assert "PINECONE_API_KEY" in os.environ.keys(), f"Error! `PINECONE_API_KEY` needs to be set in your environment!"
        assert "OPENAI_API_KEY" in os.environ.keys(), f"Error! `OPENAI_API_KEY` needs to be set in your environment!"

        # Create Pinecone Index object
        self.index_name = 'me-2-0-index'
        pinecone.init(api_key=PINECONE_API_KEY, environment="us-central1-gcp")
        self.index = pinecone.Index(self.index_name)
        self.model_name = 'text-embedding-ada-002'
        self.embedding = OpenAIEmbeddings(model=self.model_name, openai_api_key=OPENAI_API_KEY)
        self.number_of_retrieval_results = number_of_retrieval_results or 3

        # Create connection to Pinecone index
        self.vectorstore = Pinecone(index=self.index, embedding_function=self.embedding.embed_query, text_key="transcript")
        logger.info("Instantiated a vectordb connection object.")

    def query(self, query: str) -> str:
        logger.debug(f"Querying vectorb db with query: `{query}` and k: `{self.number_of_retrieval_results}`.")
        results = self.vectorstore.similarity_search(query=query, k=self.number_of_retrieval_results)
        output = " ".join([r.page_content for r in results])
        return output
