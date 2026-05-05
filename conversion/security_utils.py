import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# 1. Carga las variables de entorno desde el archivo .env
load_dotenv()


def get_cipher_suite():
    """
    Configura y retorna el objeto de cifrado usando la ENCRYPTION_KEY.
    """
    # Recupera la llave desde los Secrets/Variables de entorno
    key = os.getenv("ENCRYPTION_KEY")

    if not key:
        # Si no hay llave, lanzamos un error para evitar procesar archivos sin protección
        raise ValueError(
            "CRITICAL ERROR: No se encontró 'ENCRYPTION_KEY'. "
            "Asegúrate de que esté en tu .env (local) o en los Secrets de GitHub."
        )

    # Fernet requiere la llave en formato bytes
    return Fernet(key.encode())


def proteger_archivo(ruta_archivo):
    """
    Cifra un archivo (PDF, HTML, etc.) y guarda la versión cifrada con extensión .enc
    """
    try:
        cipher_suite = get_cipher_suite()

        # Leer el contenido original del archivo
        with open(ruta_archivo, "rb") as f:
            datos_originales = f.read()

        # Aplicar el cifrado
        datos_cifrados = cipher_suite.encrypt(datos_originales)

        # Guardar el archivo cifrado
        nueva_ruta = f"{ruta_archivo}.enc"
        with open(nueva_ruta, "wb") as f:
            f.write(datos_cifrados)

        print(f"Éxito: Archivo protegido en {nueva_ruta}")
        return nueva_ruta

    except Exception as e:
        print(f"Error de seguridad al proteger archivo: {e}")
        return None


def descifrar_archivo(ruta_archivo_enc, ruta_salida):
    """
    Toma un archivo .enc y lo restaura a su formato original.
    """
    try:
        cipher_suite = get_cipher_suite()

        with open(ruta_archivo_enc, "rb") as f:
            datos_cifrados = f.read()

        datos_originales = cipher_suite.decrypt(datos_cifrados)

        with open(ruta_salida, "wb") as f:
            f.write(datos_originales)

        return ruta_salida
    except Exception as e:
        print(f"Error al descifrar el archivo: {e}")
        return None