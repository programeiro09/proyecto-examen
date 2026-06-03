# Sistemas de Gestión Empresarial
**José Vicente Carratalá Sanchis**

---

## Tabla de contenidos

1. [Tipos de sistemas de gestión empresarial](#1-tipos-de-sistemas-de-gestión-empresarial)
2. [Características y clasificación del software](#2-características-y-clasificación-del-software)
3. [Gestores de bases de datos utilizados](#3-gestores-de-bases-de-datos-utilizados)
4. [Operaciones de documentación](#4-operaciones-de-documentación)
5. [Módulos del sistema](#5-módulos-del-sistema)
6. [Parámetros configurables](#6-parámetros-configurables)
7. [Integración con otros sistemas](#7-integración-con-otros-sistemas)
8. [Entornos de desarrollo y tecnologías](#8-entornos-de-desarrollo-y-tecnologías)
9. [Tablas y campos de la base de datos](#9-tablas-y-campos-de-la-base-de-datos)
10. [Consultas a la base de datos](#10-consultas-a-la-base-de-datos)
11. [Interfaces de acceso a datos](#11-interfaces-de-acceso-a-datos)
12. [Informes y gráficas](#12-informes-y-gráficas)

---

## 1. Tipos de sistemas de gestión empresarial

Los sistemas de gestión empresarial se agrupan en las siguientes categorías principales:

| Siglas | Nombre | Descripción |
|--------|--------|-------------|
| **ERP** | Enterprise Resource Planning | Integra todos los procesos clave de una empresa: contabilidad, producción, compras, RRHH. Ej.: SAP, Odoo. |
| **CRM** | Customer Relationship Management | Gestiona la relación con clientes, ventas y marketing. Ej.: Salesforce, HubSpot. |
| **SCM** | Supply Chain Management | Gestiona la cadena de suministro: proveedores, logística y distribución. |
| **HRM / HRMS** | Human Resource Management System | Gestiona recursos humanos: nóminas, contratación, evaluaciones. |
| **BI** | Business Intelligence | Analiza datos empresariales para apoyar decisiones. Ej.: Power BI, Tableau. |
| **KMS** | Knowledge Management System | Captura, organiza y permite consultar el conocimiento interno de la organización. |
| **DMS** | Document Management System | Gestiona documentos digitales: almacenamiento, versiones, búsqueda. |
| **ECM** | Enterprise Content Management | Gestión ampliada de contenidos no estructurados (documentos, correos, imágenes). |
| **BPM** | Business Process Management | Modela, automatiza y optimiza procesos de negocio. |
| **WMS** | Warehouse Management System | Controla operaciones en almacenes: entradas, salidas, inventario. |

---

## 2. Características y clasificación del software

### Nombre del proyecto: **Second Brain Lite**

**Second Brain Lite** es un sistema de consulta inteligente de documentos basado en RAG (*Retrieval-Augmented Generation*). Permite cargar documentos PDF y hacerles preguntas en lenguaje natural, obteniendo respuestas contextualizadas generadas por un modelo de lenguaje local.

### Clasificación

El sistema se encuadra principalmente en dos categorías:

- **KMS (Knowledge Management System):** Su función principal es capturar el conocimiento contenido en documentos y hacerlo consultable de forma inteligente.
- **DMS (Document Management System):** Ingiere, indexa y recupera documentos de forma estructurada.

Adicionalmente incorpora características propias de los sistemas de **BI** al permitir extraer conclusiones y respuestas analíticas del contenido documental.

### Características principales

- Procesamiento de documentos PDF de forma automática.
- Búsqueda semántica mediante vectores de embeddings.
- Generación de respuestas en lenguaje natural con citas de fuente.
- Interfaz conversacional tipo chatbot.
- Funcionamiento completamente local (sin dependencias de servicios cloud).
- Respuestas deterministas configurables mediante temperatura del LLM.

---

## 3. Gestores de bases de datos utilizados

### ChromaDB (con SQLite como motor subyacente)

El proyecto utiliza **ChromaDB** como base de datos vectorial. Internamente, ChromaDB persiste sus datos usando **SQLite** (archivo `chroma_db/chroma.sqlite3`).

| Capa | Tecnología | Rol |
|------|-----------|-----|
| Base de datos vectorial | ChromaDB | Almacena embeddings y permite búsqueda por similitud |
| Motor de persistencia | SQLite | Motor relacional interno de ChromaDB |

**Por qué ChromaDB:**

- Es la solución estándar para proyectos RAG con LangChain.
- Permite búsqueda por similitud coseno sobre vectores de alta dimensión (768 dimensiones en `nomic-embed-text`).
- Funciona de forma completamente local, sin servidor externo.
- Se integra de forma nativa con LangChain mediante `langchain_chroma`.
- Es ligera y no requiere instalación ni configuración de servidor adicional.

**Por qué no una base de datos relacional tradicional:**

Los datos almacenados son vectores numéricos de alta dimensión, no registros tabulares. Una base de datos relacional como PostgreSQL o MySQL no puede realizar búsquedas de similitud semántica de forma eficiente sin extensiones específicas.

---

## 4. Operaciones de documentación que contiene la aplicación

La aplicación implementa el ciclo completo de gestión documental siguiendo el patrón RAG:

### 4.1 Ingesta (módulo `ingest.py`)

| Operación | Descripción |
|-----------|-------------|
| **Carga** | Lectura de todos los archivos `.pdf` en la carpeta `./docs` usando `PyPDFLoader`. |
| **Fragmentación** | División del texto en chunks de 512 caracteres con solapamiento de 64 caracteres mediante `RecursiveCharacterTextSplitter`. |
| **Cifrado** | Cada chunk se cifra con Fernet (AES-128) antes de almacenarse. |
| **Vectorización** | Generación de embeddings para cada chunk con el modelo `nomic-embed-text` vía Ollama. |
| **Indexación** | Almacenamiento de chunks cifrados y sus vectores en ChromaDB con metadatos de fuente y página. |

### 4.2 Consulta (módulo `query.py`)

| Operación | Descripción |
|-----------|-------------|
| **Recuperación** | Búsqueda de los 4 chunks más similares semánticamente a la pregunta del usuario. |
| **Descifrado** | Los chunks recuperados se descifran con Fernet antes de pasarlos al LLM. |
| **Generación** | El LLM (`llama3.2:3b`) genera una respuesta basándose exclusivamente en los chunks descifrados. |
| **Citación** | Se devuelven las fuentes (nombres de archivo) de los documentos consultados. |

### 4.3 Presentación (módulo `app.py`)

| Operación | Descripción |
|-----------|-------------|
| **Interfaz** | Chatbot web con historial de conversación construido con Gradio. |
| **Visualización de fuentes** | Las fuentes citadas se muestran al final de cada respuesta en negrita. |

---

## 5. Módulos del sistema

El sistema está estructurado en tres módulos funcionales más dos directorios de datos:

```
proyecto-ollama/
├── ingest.py        # Módulo de ingesta de documentos
├── query.py         # Módulo de consulta y cadena RAG
├── app.py           # Módulo de interfaz de usuario
├── crypto_utils.py  # Módulo de cifrado/descifrado Fernet
├── docs/            # Almacén de documentos PDF fuente
└── chroma_db/       # Base de datos vectorial persistente
```

### Módulo 1: `ingest.py` — Ingesta de documentos

**Función:** Preprocesa los PDFs, cifra los chunks y construye el índice vectorial.

**Componentes internos:**
- `PyPDFLoader`: carga y extrae texto de PDFs página a página.
- `RecursiveCharacterTextSplitter`: divide el texto en fragmentos manejables.
- `crypto_utils.cifrar`: cifra el contenido de cada chunk con Fernet antes de almacenarlo.
- `OllamaEmbeddings`: genera los vectores numéricos de cada fragmento.
- `Chroma.from_documents()`: persiste los fragmentos cifrados y vectores en ChromaDB.

### Módulo 2: `query.py` — Cadena de consulta RAG

**Función:** Define y devuelve la cadena de recuperación y generación de respuestas.

**Componentes internos:**
- `OllamaEmbeddings`: vectoriza la pregunta del usuario para la búsqueda.
- `DecryptingRetriever`: recupera chunks de ChromaDB y los descifra automáticamente.
- `OllamaLLM`: genera la respuesta con el modelo `llama3.2:3b`.
- `PromptTemplate`: define el prompt del sistema.
- `RetrievalQA`: cadena que combina retriever + LLM.

### Módulo 3: `app.py` — Interfaz de usuario

**Función:** Expone la funcionalidad como aplicación web interactiva.

**Componentes internos:**
- `gr.Blocks`: contenedor principal de la interfaz Gradio.
- `gr.Chatbot`: widget que muestra el historial de conversación.
- `gr.Textbox` + `gr.Button`: entrada de preguntas y botón de envío.
- Función `ask()`: orquesta la llamada a la cadena y actualiza el historial.

### Módulo 4: `crypto_utils.py` — Cifrado Fernet

**Función:** Gestiona la clave simétrica y expone las funciones de cifrado y descifrado.

**Componentes internos:**
- `generar_clave()`: genera y persiste una clave Fernet aleatoria en `secret.key`.
- `cargar_clave()`: carga la clave desde disco.
- `cifrar(texto)`: cifra un string y devuelve un token cifrado.
- `descifrar(token)`: descifra el token y devuelve el texto original.

---

## 6. Parámetros configurables

### Parámetros en `ingest.py`

| Parámetro | Valor actual | Descripción |
|-----------|-------------|-------------|
| `DOCS_PATH` | `"./docs"` | Directorio donde se leen los PDFs a indexar |
| `DB_PATH` | `"./chroma_db"` | Directorio donde se persiste la base de datos vectorial |
| `chunk_size` | `512` | Tamaño máximo de cada fragmento de texto en caracteres |
| `chunk_overlap` | `64` | Solapamiento entre fragmentos consecutivos para mantener contexto |
| `separators` | `["\n\n", "\n", " "]` | Jerarquía de separadores para el corte de texto |
| `model` (embeddings) | `"nomic-embed-text"` | Modelo de Ollama para generar embeddings |

### Parámetros en `query.py`

| Parámetro | Valor actual | Descripción |
|-----------|-------------|-------------|
| `DB_PATH` | `"./chroma_db"` | Directorio de la base de datos vectorial a consultar |
| `model` (embeddings) | `"nomic-embed-text"` | Modelo de embeddings para vectorizar la pregunta |
| `model` (LLM) | `"llama3.2:3b"` | Modelo de lenguaje para generar respuestas |
| `temperature` | `0.1` | Temperatura del LLM (0 = determinista, 1 = creativo) |
| `num_ctx` | `2048` | Tamaño de la ventana de contexto del LLM en tokens |
| `k` | `4` | Número de chunks más relevantes a recuperar por consulta |
| `search_type` | `"similarity"` | Tipo de búsqueda vectorial (similitud coseno) |

### Parámetros en `crypto_utils.py`

| Parámetro | Valor actual | Descripción |
|-----------|-------------|-------------|
| `KEY_FILE` | `"secret.key"` | Ruta del archivo donde se persiste la clave Fernet |

### Parámetros en `app.py`

| Parámetro | Valor actual | Descripción |
|-----------|-------------|-------------|
| `title` | `"Second Brain"` | Título de la pestaña del navegador |
| `height` | `420` | Altura en píxeles del widget del chatbot |
| `placeholder` | `"Pregunta algo..."` | Texto de ayuda del campo de entrada |

---

## 7. Integración con otros sistemas

El sistema se comunica con servicios externos mediante API HTTP local:

### Entrada: Ollama (servidor de inferencia local)

```
Aplicación Python ──HTTP──> Ollama (localhost:11434)
                              ├── nomic-embed-text  (embeddings)
                              └── llama3.2:3b       (generación)
```

- **Protocolo:** HTTP REST (API de Ollama).
- **Dirección:** `http://localhost:11434` (por defecto).

### Entrada: Sistema de archivos

- La aplicación lee documentos PDF del directorio `./docs`.

### Salida: Interfaz web Gradio

- Gradio lanza un servidor web local (`http://127.0.0.1:7860`).

### Resumen de flujo de datos

```
PDF en ./docs
     │
     ▼
[ingest.py] ──cifra chunks──> crypto_utils ──embeddings vía Ollama──> ChromaDB
                                                       │
                                       Pregunta del usuario (navegador)
                                                       │
                                                  [app.py]
                                                       │
                                                  [query.py]
                                             ┌─────────┴─────────┐
                                      Retrieval               Decrypt
                                    (ChromaDB)           (crypto_utils)
                                             └─────────┬─────────┘
                                                      LLM (Ollama)
                                                       │
                                             Respuesta + fuentes
                                                       │
                                          Navegador del usuario
```

---

## 8. Entornos de desarrollo y tecnologías utilizadas

### Lenguaje

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Python** | 3.14 | Lenguaje principal de toda la aplicación |

### Frameworks y librerías principales

| Librería | Uso |
|----------|-----|
| **LangChain** | Framework de orquestación para cadenas RAG |
| **langchain_ollama** | Integración LangChain ↔ Ollama |
| **langchain_chroma** | Integración LangChain ↔ ChromaDB |
| **Gradio** | Framework para la interfaz web del chatbot |
| **ChromaDB** | Base de datos vectorial |
| **cryptography (Fernet)** | Cifrado simétrico AES-128 de los chunks |
| **bcrypt** | Hasheado seguro de contraseñas |
| **PyPDFLoader** | Extracción de texto desde archivos PDF |

### Motor de inferencia

| Tecnología | Uso |
|-----------|-----|
| **Ollama** | Servidor local de inferencia de modelos LLM |
| **nomic-embed-text** | Modelo de embeddings (768 dimensiones) |
| **llama3.2:3b** | Modelo de lenguaje generativo |

### Entorno de desarrollo

| Elemento | Detalle |
|----------|---------|
| **Sistema operativo** | macOS (Darwin 25.0.0) |
| **Entorno virtual** | Python venv (`.venv/`) |
| **Editor** | Visual Studio Code |

---

## 9. Tablas y campos de la base de datos

ChromaDB utiliza SQLite internamente. Las tablas principales del archivo `chroma_db/chroma.sqlite3` son:

### Tabla: `collections`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | TEXT (UUID) | Identificador único de la colección |
| `name` | TEXT | Nombre de la colección |
| `config_json_str` | TEXT | Configuración de la colección en formato JSON |
| `dimension` | INTEGER | Dimensión de los vectores (768 para nomic-embed-text) |

### Tabla: `embeddings`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | TEXT | Identificador único del embedding |
| `collection_id` | TEXT | FK referencia a `collections` |
| `embedding` | BLOB | Vector numérico del fragmento de texto |
| `document` | TEXT | Texto del fragmento (chunk) **cifrado con Fernet** |

### Tabla: `embedding_metadata`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | TEXT | FK referencia al embedding |
| `key` | TEXT | Nombre del metadato (ej.: `"source"`, `"page"`) |
| `string_value` | TEXT | Valor del metadato si es texto |
| `int_value` | INTEGER | Valor del metadato si es entero (ej.: número de página) |

### Metadatos almacenados por documento

| Metadato | Valor ejemplo | Descripción |
|----------|--------------|-------------|
| `source` | `"docs/Propuesta_ERP.pdf"` | Ruta del archivo PDF de origen |
| `page` | `3` | Número de página del PDF del que proviene el chunk |

---

## 10. Consultas a la base de datos que se realizan en la aplicación

### Operación de escritura — Ingesta (`ingest.py`)

```python
Chroma.from_documents(
    documents=chunks,       # chunks con page_content CIFRADO
    embedding=embeddings,
    persist_directory=DB_PATH
)
```

**Cuándo se ejecuta:** Solo al correr `ingest.py`.

### Operación de lectura — Búsqueda por similitud (`query.py`)

```python
db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)
```

Devuelve los 4 chunks con mayor similitud coseno al vector de la pregunta. El contenido viene cifrado y `DecryptingRetriever` lo descifra antes de usarlo.

**Cuándo se ejecuta:** En cada pregunta del usuario.

### Operación de lectura — Carga del índice (`query.py`)

```python
Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
```

**Cuándo se ejecuta:** Al arrancar la aplicación, una sola vez.

---

## 11. Interfaces de acceso a datos en la aplicación

El proyecto utiliza un patrón de acceso a datos por capas de abstracción:

### Capa 1: ORM vectorial — LangChain Chroma

`langchain_chroma.Chroma` actúa como capa de abstracción sobre ChromaDB, exponiendo métodos de alto nivel sin SQL manual.

### Capa 2: Descifrado — DecryptingRetriever

```
ChromaDB (chunks cifrados) → DecryptingRetriever → chunks en claro → LLM
```

Clase wrapper que intercepta los documentos recuperados y los descifra automáticamente.

### Capa 3: Embeddings — OllamaEmbeddings

```
Texto (str) → OllamaEmbeddings.embed_query() → Vector [float] (768 dims)
```

### Capa 4: Cadena de recuperación — RetrievalQA

```
Pregunta → [Embedding] → [DecryptingRetriever] → [Prompt] → [LLM] → Respuesta
```

### Capa 5: Carga de documentos — PyPDFLoader

```
Archivo PDF → PyPDFLoader.load() → List[Document(page_content, metadata)]
```

---

## 12. Informes y gráficas que genera la aplicación

**Second Brain Lite** no genera informes estadísticos ni gráficas en su versión actual.

Produce las siguientes salidas estructuradas de información:

### Respuestas con citación de fuentes

```
La propuesta incluye un módulo de gestión de contratos con seguimiento 
de plazos y alertas automáticas.

**Fuentes:** docs/Propuesta_ERP_LeBratelier_Saymar.pdf
```

### Historial de conversación

La interfaz mantiene un historial visual de toda la sesión de consultas, con mensajes diferenciados por rol (usuario / asistente).

### Salidas en consola (modo desarrollo)

Al ejecutar `ingest.py`:

```
→ Encontrados 1 PDFs
  Cargando: Propuesta_ERP_LeBratelier_Saymar.pdf
→ 87 chunks de 12 páginas
✓ Chunks cifrados con Fernet (AES-128)
✓ Índice cifrado guardado en ./chroma_db
```

### Posibles extensiones futuras

- Frecuencia de consultas por documento fuente.
- Mapa de calor de las secciones más consultadas.
- Dashboard con estadísticas de uso.
- Exportación de conversaciones en PDF o CSV.
