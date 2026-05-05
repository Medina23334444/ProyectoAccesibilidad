import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# Obtenemos la llave
SECRET_KEY = os.getenv("ENCRYPTION_KEY")

if SECRET_KEY is None:
    raise ValueError("Error: No se encontró 'ENCRYPTION_KEY' en las variables de entorno o el archivo .env")

# Inicializamos el sistema de cifrado
cipher_suite = Fernet(SECRET_KEY.encode())  # .encode() asegura que sea bytes


def proteger_archivo(ruta_archivo):
    """Cifra un archivo PDF o HTML y genera una versión .enc"""
    try:
        with open(ruta_archivo, "rb") as f:
            datos = f.read()

        datos_cifrados = cipher_suite.encrypt(datos)

        nueva_ruta = ruta_archivo + ".enc"
        with open(nueva_ruta, "wb") as f:
            f.write(datos_cifrados)

        print(f"Archivo protegido con éxito: {nueva_ruta}")
        return nueva_ruta
    except Exception as e:
        print(f"Error al proteger el archivo: {e}")
        return None