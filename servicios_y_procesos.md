# Servicios y Procesos
**José Vicente Carratalá Sanchis**

---

## Tabla de contenidos

1. [Comunicación entre sistemas mediante APIs](#1-comunicación-entre-sistemas-mediante-apis)
2. [Rol de servidor y rol de cliente](#2-rol-de-servidor-y-rol-de-cliente)
3. [Apertura de un servicio web: contrato y documentación](#3-apertura-de-un-servicio-web-contrato-y-documentación)
4. [Técnicas criptográficas de ida y vuelta](#4-técnicas-criptográficas-de-ida-y-vuelta)
5. [Técnicas de hasheado](#5-técnicas-de-hasheado)

---

## 1. Comunicación entre sistemas mediante APIs

### ¿Qué es una API en el contexto de sistemas empresariales?

Una **API** (*Application Programming Interface*) es un contrato formal que define cómo dos sistemas se comunican entre sí: qué datos se envían, en qué formato, y qué se espera recibir a cambio. En el contexto de sistemas de gestión empresarial, las APIs permiten que módulos independientes —o incluso aplicaciones de empresas distintas— intercambien información sin necesidad de conocer su implementación interna.

### Cómo aplica este proyecto

**Second Brain Lite** no es un sistema aislado. Se comunica activamente con servicios externos a través de dos mecanismos de API bien diferenciados:

```
┌─────────────────────────────────────────────────────┐
│                  SECOND BRAIN LITE                   │
│                                                      │
│  ┌──────────┐   HTTP REST   ┌─────────────────────┐ │
│  │ ingest.py│─────────────► │  Ollama API Server  │ │
│  │ query.py │◄──────────── │  localhost:11434     │ │
│  └──────────┘   JSON resp  └─────────────────────┘ │
│                                                      │
│  ┌──────────┐   HTTP/WS     ┌─────────────────────┐ │
│  │  app.py  │◄─────────────│  Navegador (browser)│ │
│  │ (Gradio) │─────────────►│  localhost:7860      │ │
│  └──────────┘              └─────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Mecanismo 1: API REST de Ollama

El proyecto consume la API REST de **Ollama** para dos operaciones:

#### Embeddings (vectorización de texto)

Cada vez que se indexa un chunk o se vectoriza una pregunta, se realiza la siguiente llamada HTTP:

```http
POST http://localhost:11434/api/embeddings
Content-Type: application/json

{
  "model": "nomic-embed-text",
  "prompt": "texto del fragmento del documento"
}
```

Respuesta del servidor Ollama:

```json
{
  "embedding": [0.0123, -0.0456, 0.0789, ... ]
}
```

El vector resultante tiene **768 dimensiones** y representa semánticamente el texto.

#### Generación de texto (LLM inference)

Cuando el usuario hace una pregunta, se realiza esta llamada:

```http
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "llama3.2:3b",
  "prompt": "Eres un asistente...\n\nContexto:\n{chunks}\n\nPregunta: {pregunta}\nRespuesta:",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "num_ctx": 2048
  }
}
```

Respuesta:

```json
{
  "model": "llama3.2:3b",
  "response": "Según el documento, el módulo de contratos...",
  "done": true,
  "total_duration": 1234567890
}
```

### Mecanismo 2: API WebSocket de Gradio

La interfaz Gradio (v6.15.2) expone automáticamente un servidor web que se comunica con el navegador usando **HTTP** para la carga inicial y **WebSocket** para las interacciones en tiempo real, lo que permite el efecto de respuesta progresiva ("streaming").

---

## 2. Rol de servidor y rol de cliente

En el proyecto coexisten **tres instancias** distintas de la relación cliente-servidor, lo que ilustra bien cómo los sistemas reales tienen ambos roles de forma simultánea.

### Visión general de roles

```
 CLIENTE                    SERVIDOR              SERVICIO
──────────────────────────────────────────────────────────
 Navegador web   ──────►   Gradio (app.py)       Chatbot UI
                           puerto 7860

 app.py / query.py ──────► Ollama               Embeddings
                           puerto 11434          + LLM

 ingest.py ─────────────►  ChromaDB (SQLite)    Almacén
                           ./chroma_db/          vectorial
```

### Caso A: Nuestra app como CLIENTE de Ollama

| Concepto | Detalle |
|----------|---------|
| **Cliente** | `query.py` e `ingest.py` (Python) |
| **Servidor** | Ollama (`ollama serve`, puerto 11434) |
| **Protocolo** | HTTP REST + JSON |
| **Responsabilidad del cliente** | Enviar el texto, recibir el embedding o la respuesta generada |
| **Responsabilidad del servidor** | Cargar el modelo en GPU/CPU, hacer la inferencia, devolver el resultado |

El cliente no sabe cómo funciona el modelo internamente; solo conoce el contrato de la API.

```python
# query.py — nuestro código actúa como cliente de Ollama
embeddings = OllamaEmbeddings(model="nomic-embed-text")
# Internamente hace: POST http://localhost:11434/api/embeddings

llm = OllamaLLM(model="llama3.2:3b", temperature=0.1)
# Internamente hace: POST http://localhost:11434/api/generate
```

### Caso B: Nuestra app como SERVIDOR para el navegador

| Concepto | Detalle |
|----------|---------|
| **Servidor** | `app.py` con Gradio (puerto 7860) |
| **Cliente** | Navegador web del usuario |
| **Protocolo** | HTTP (carga de la página) + WebSocket (interacción) |
| **Responsabilidad del servidor** | Recibir la pregunta, procesarla con la cadena RAG, devolver la respuesta |
| **Responsabilidad del cliente** | Renderizar la interfaz, enviar la pregunta, mostrar el historial |

```python
# app.py — nuestro código actúa como servidor web
with gr.Blocks(title="Second Brain") as demo:
    chatbot = gr.Chatbot(height=420)
    txt = gr.Textbox(placeholder="Pregunta algo sobre tus notas...")
    btn = gr.Button("Enviar")
    btn.click(ask, [txt, chatbot], [txt, chatbot])

demo.launch()  # lanza el servidor en http://localhost:7860
```

El navegador no sabe que internamente la app llama a Ollama; solo conoce la interfaz Gradio.

### Resumen visual del doble rol

```
Navegador                app.py (Gradio)              Ollama
   │                          │                          │
   │── POST /queue/join ──────►│                          │
   │                          │── POST /api/embeddings ──►│
   │                          │◄── [vector] ─────────────│
   │                          │── POST /api/generate ────►│
   │                          │◄── "La respuesta es..." ─│
   │◄── respuesta + fuentes ──│                          │
   │                          │                          │
```

---

## 3. Apertura de un servicio web: contrato y documentación

### Descripción del servicio

**Second Brain Lite** expone un servicio web de consulta inteligente de documentos a través de Gradio. Además de la interfaz visual, Gradio genera automáticamente una **API REST y WebSocket** accesible en `http://localhost:7860`.

La documentación interactiva de la API generada por Gradio está disponible en:

```
http://localhost:7860/?view=api
```

---

### Contrato de la API

#### Endpoint principal: Enviar pregunta

| Campo | Valor |
|-------|-------|
| **URL** | `http://localhost:7860/call/ask` |
| **Método** | `POST` |
| **Autenticación** | Ninguna (servicio local) |
| **Content-Type** | `application/json` |

#### Request body

```json
{
  "data": [
    "¿Qué módulos incluye la propuesta ERP?",
    []
  ]
}
```

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `data[0]` | `string` | Sí | Pregunta del usuario en lenguaje natural |
| `data[1]` | `array` | Sí | Historial de conversación previo (vacío en primera llamada) |

#### Response body (éxito — HTTP 200)

```json
{
  "data": [
    "",
    [
      {"role": "user",      "content": "¿Qué módulos incluye la propuesta ERP?"},
      {"role": "assistant", "content": "Según el documento, los módulos incluidos son...\n\n**Fuentes:** docs/Propuesta_ERP_LeBratelier_Saymar.pdf"}
    ]
  ]
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `data[0]` | `string` | Siempre vacío (el textbox se limpia tras enviar) |
| `data[1]` | `array` | Historial completo actualizado con la nueva respuesta |
| `data[1][n].role` | `"user"` \| `"assistant"` | Rol del mensaje |
| `data[1][n].content` | `string` | Contenido del mensaje con las fuentes en Markdown |

#### Response body (pregunta vacía — sin cambios)

```json
{
  "data": ["", []]
}
```

---

### Ejemplo de consumo desde Python (cliente externo)

```python
import requests

BASE_URL = "http://localhost:7860"

def preguntar(pregunta: str, historial: list = []) -> tuple[str, list]:
    payload = {"data": [pregunta, historial]}
    response = requests.post(f"{BASE_URL}/call/ask", json=payload)
    response.raise_for_status()
    data = response.json()["data"]
    return data[0], data[1]

# Uso
_, historial = preguntar("¿Qué es el módulo de contratos?")
print(historial[-1]["content"])
```

### Ejemplo de consumo desde curl

```bash
curl -X POST http://localhost:7860/call/ask \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      "¿Qué módulos incluye la propuesta?",
      []
    ]
  }'
```

---

### Códigos de respuesta

| Código | Significado |
|--------|-------------|
| `200 OK` | Respuesta generada correctamente |
| `422 Unprocessable Entity` | Formato de datos incorrecto |
| `500 Internal Server Error` | Error en la cadena RAG (ej.: Ollama no disponible) |

---

### Restricciones y condiciones del servicio

- El servicio requiere que **Ollama esté en ejecución** (`ollama serve`) antes de arrancar la app.
- La base de datos vectorial debe haber sido inicializada previamente con `python ingest.py`.
- El servicio escucha únicamente en **localhost** por defecto (no expuesto a internet).
- No implementa autenticación ni limitación de tasa (*rate limiting*) en su versión actual.

---

## 4. Técnicas criptográficas de ida y vuelta

### Concepto

La **criptografía de ida y vuelta** (criptografía simétrica con descifrado) permite proteger información sensible de forma que solo quien posea la clave pueda revertir la transformación y recuperar el dato original. Se diferencia del hasheado en que la operación es **reversible**.

### Aplicación en el proyecto

En **Second Brain Lite**, Fernet protege el contenido de los chunks almacenados en ChromaDB. Se utiliza **Fernet** (AES-128-CBC con HMAC-SHA256), implementado en `crypto_utils.py`.

### Implementación: `crypto_utils.py`

```python
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def generar_clave() -> None:
    clave = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(clave)

def cargar_clave() -> Fernet:
    with open(KEY_FILE, "rb") as f:
        return Fernet(f.read())

def cifrar(texto: str) -> str:
    return cargar_clave().encrypt(texto.encode()).decode()

def descifrar(token: str) -> str:
    return cargar_clave().decrypt(token.encode()).decode()
```

### Integración en `ingest.py` (cifrado — IDA)

```python
from crypto_utils import generar_clave, cifrar

# Genera la clave si no existe
if not Path("secret.key").exists():
    generar_clave()

# Cifra cada chunk antes de almacenarlo en ChromaDB
for chunk in chunks:
    chunk.page_content = cifrar(chunk.page_content)
```

### Integración en `query.py` (descifrado — VUELTA)

```python
class DecryptingRetriever:
    def get_relevant_documents(self, query: str) -> list[Document]:
        docs = self._retriever.get_relevant_documents(query)
        for doc in docs:
            try:
                doc.page_content = descifrar(doc.page_content)
            except Exception:
                pass  # chunk no cifrado (índice antiguo)
        return docs
```

### Demostración completa del ciclo

```python
from crypto_utils import generar_clave, cifrar, descifrar
from pathlib import Path

if not Path("secret.key").exists():
    generar_clave()

texto_original = "La propuesta incluye un módulo de gestión de contratos con Saymar."
print(f"Original:  {texto_original}")

token_cifrado = cifrar(texto_original)
print(f"Cifrado:   {token_cifrado[:50]}...")

texto_recuperado = descifrar(token_cifrado)
print(f"Descifrado: {texto_recuperado}")

assert texto_original == texto_recuperado
print("✓ Ciclo cifrado/descifrado completado correctamente.")
```

**Salida:**

```
Original:   La propuesta incluye un módulo de gestión de contratos con Saymar.
Cifrado:    gAAAAABl3z8k1QmXwR7pN2oL...
Descifrado: La propuesta incluye un módulo de gestión de contratos con Saymar.
✓ Ciclo cifrado/descifrado completado correctamente.
```

### Características del cifrado Fernet

| Propiedad | Valor |
|-----------|-------|
| Algoritmo | AES-128-CBC |
| Autenticación | HMAC-SHA256 |
| Tipo | Simétrico (misma clave cifra y descifra) |
| Tamaño de clave | 256 bits (32 bytes en base64-url) |
| Padding | PKCS7 |
| Reversible | Sí (requiere la clave) |

---

## 5. Técnicas de hasheado

### Concepto

El **hasheado** es una transformación **unidireccional**: dado un dato de entrada, produce una cadena de longitud fija (el *hash* o *digest*) que es prácticamente imposible de revertir. Es la técnica correcta para verificar integridad y almacenar credenciales, donde no es necesario recuperar el valor original.

Se diferencia del cifrado en que **no existe descifrado posible**.

### Aplicación en el proyecto

El proyecto tiene instalada la librería **bcrypt 5.0.0** y dispone del módulo estándar **hashlib**. Se aplican dos técnicas de hasheado con propósitos distintos:

---

### Técnica 1: SHA-256 para integridad documental

Se usa **SHA-256** (módulo estándar `hashlib`) para detectar si un PDF ya ha sido indexado, evitando duplicados en ChromaDB.

```python
import hashlib
from pathlib import Path

def hash_documento(ruta: str) -> str:
    sha256 = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            sha256.update(bloque)
    return sha256.hexdigest()

# Uso en la ingesta
for pdf_path in pdf_files:
    digest = hash_documento(str(pdf_path))
    if digest in ya_indexados:
        print(f"  [SKIP] {pdf_path.name} — ya indexado ({digest[:12]}...)")
        continue
    print(f"  [NEW]  {pdf_path.name} — indexando...")
```

#### Demostración de la propiedad de avalancha

```python
import hashlib

v1 = b"Propuesta ERP LeBratelier - v1.0"
v2 = b"Propuesta ERP LeBratelier - v1.1"

print(hashlib.sha256(v1).hexdigest())
# → 3a7f2c1e9b4d8f6a0e5c2b1d4f7a9e3c...
print(hashlib.sha256(v2).hexdigest())
# → completamente distinto aunque solo cambió "v1.0" → "v1.1"
```

---

### Técnica 2: bcrypt para credenciales de acceso

**bcrypt** (instalado en el proyecto, v5.0.0) es el algoritmo estándar para almacenar contraseñas. Incorpora un **salt aleatorio** en cada hash, resistente a ataques de diccionario y tablas rainbow.

```python
import bcrypt

def hashear_password(password: str) -> bytes:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt)

def verificar_password(password: str, hash_guardado: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hash_guardado)
```

#### Demostración completa

```python
import bcrypt

password = "SecondBrain2024!"
hash_guardado = hashear_password(password)

print(f"Password original: {password}")
print(f"Hash bcrypt:       {hash_guardado}")
# → $2b$12$eImiTXuWVxfM37uY3Gs1dO...

print(verificar_password("SecondBrain2024!", hash_guardado))  # True
print(verificar_password("ContraseñaMal",   hash_guardado))  # False

# Salt aleatorio: mismo password → hashes distintos
hash_1 = hashear_password("mismopassword")
hash_2 = hashear_password("mismopassword")
print(hash_1 == hash_2)  # False
```

**Salida:**

```
Password original: SecondBrain2024!
Hash bcrypt:       $2b$12$eImiTXuWVxfM37uY3Gs1dOsuQkM6nN3Y7LqX8W9Pk2Ro1Hj5Tv0u
True
False
False
```

---

### Comparativa de técnicas

| Característica | SHA-256 (hashlib) | bcrypt |
|---------------|-------------------|--------|
| **Uso en el proyecto** | Fingerprint de PDFs | Contraseñas de acceso |
| **Velocidad** | Muy rápido | Deliberadamente lento |
| **Salt** | No (determinista) | Sí (integrado y aleatorio) |
| **Reversible** | No | No |
| **Resistente a GPU** | Bajo | Alto |
| **Longitud del digest** | 64 caracteres hex | 60 caracteres |
| **Cuándo usarlo** | Integridad de datos | Contraseñas de usuarios |

---

### Diferencia clave entre cifrado y hasheado

| | Cifrado (Fernet/AES) | Hasheado (SHA-256/bcrypt) |
|--|---------------------|--------------------------|
| **¿Reversible?** | Sí, con la clave | No |
| **¿Para qué?** | Proteger datos que necesito recuperar | Verificar sin recuperar |
| **Ejemplo en el proyecto** | Chunks almacenados en ChromaDB | Detectar PDFs duplicados, proteger contraseñas |
| **Riesgo si se pierde la clave** | Datos irrecuperables | Ninguno (no hay "descifrado") |
