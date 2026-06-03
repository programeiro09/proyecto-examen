from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def generar_clave() -> None:
    clave = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(clave)
    print(f"✓ Clave generada y guardada en {KEY_FILE}")

def cargar_clave() -> Fernet:
    with open(KEY_FILE, "rb") as f:
        return Fernet(f.read())

def cifrar(texto: str) -> str:
    return cargar_clave().encrypt(texto.encode()).decode()

def descifrar(token: str) -> str:
    return cargar_clave().decrypt(token.encode()).decode()
