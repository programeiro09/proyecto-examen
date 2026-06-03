from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from crypto_utils import generar_clave, cifrar

DOCS_PATH = "./docs"
DB_PATH = "./chroma_db"

def ingest():
    # Generar clave si no existe
    if not Path("secret.key").exists():
        generar_clave()

    pdf_files = list(Path(DOCS_PATH).glob("**/*.pdf"))
    print(f"→ Encontrados {len(pdf_files)} PDFs")

    docs = []
    for pdf_path in pdf_files:
        print(f"  Cargando: {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(docs)
    print(f"→ {len(chunks)} chunks de {len(docs)} páginas")

    # Cifrar el contenido de cada chunk antes de almacenarlo
    for chunk in chunks:
        chunk.page_content = cifrar(chunk.page_content)
    print("✓ Chunks cifrados con Fernet (AES-128)")

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    print(f"✓ Índice cifrado guardado en {DB_PATH}")

if __name__ == "__main__":
    ingest()
