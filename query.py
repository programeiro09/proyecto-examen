from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from crypto_utils import descifrar

DB_PATH = "./chroma_db"

PROMPT_TEMPLATE = """Eres un asistente que responde basándose únicamente en el contexto.
Si la respuesta no está en el contexto, di "No tengo información sobre eso."

Contexto:
{context}

Pregunta: {question}
Respuesta:"""

class DecryptingRetriever:
    """Envuelve el retriever de Chroma y descifra los documentos recuperados."""

    def __init__(self, base_retriever):
        self._retriever = base_retriever

    def get_relevant_documents(self, query: str) -> list[Document]:
        docs = self._retriever.get_relevant_documents(query)
        for doc in docs:
            try:
                doc.page_content = descifrar(doc.page_content)
            except Exception:
                pass  # chunk no cifrado (índice antiguo), se usa tal cual
        return docs

    # Compatibilidad con la cadena RetrievalQA
    def __getattr__(self, name):
        return getattr(self._retriever, name)

def get_qa_chain():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

    base_retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    retriever = DecryptingRetriever(base_retriever)

    llm = OllamaLLM(
        model="llama3.2:3b",
        temperature=0.1,
        num_ctx=2048
    )

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )