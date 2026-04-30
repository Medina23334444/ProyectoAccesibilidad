# conversion/crypto_utils.py
# Implementación ABI: Cifrado AES-256-GCM + Argon2id

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets


# ─── AES-256-GCM: Cifrado de archivos temporales ───────────────────────────

def cifrar_archivo_temporal(datos: bytes, clave: bytes) -> bytes:
    """
    Cifra datos en memoria usando AES-256-GCM.
    Retorna: nonce(12 bytes) + ciphertext + tag
    """
    aesgcm = AESGCM(clave)
    nonce = os.urandom(12)  # 96 bits, único por operación
    datos_cifrados = aesgcm.encrypt(nonce, datos, None)
    return nonce + datos_cifrados  # guardamos nonce junto al ciphertext


def descifrar_archivo_temporal(datos_cifrados: bytes, clave: bytes) -> bytes:
    if len(clave) != 32:
        raise ValueError(f"Clave AES-256 debe ser 32 bytes, recibido: {len(clave)}")
    aesgcm = AESGCM(clave)
    nonce = datos_cifrados[:12]
    ciphertext = datos_cifrados[12:]
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError("Integridad comprometida: el archivo fue alterado o la clave es incorrecta")


# ─── Argon2id: Hash de tokens de sesión ────────────────────────────────────

# Configuración OWASP 2024
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32,
    salt_len=16  # Salt 128 bits — generado automáticamente
)


def generar_token_sesion() -> str:
    """Token único de 256 bits — identifica cada conversión."""
    return secrets.token_urlsafe(32)


def hashear_token(token: str) -> str:
    """
    Genera hash Argon2id con salt embebido.
    Resultado: $argon2id$v=19$m=65536,t=3,p=1$<salt_base64>$<hash_base64>
    El salt diferente en cada llamada invalida Rainbow Tables.
    """
    return _ph.hash(token)


def verificar_token(token: str, hash_guardado: str) -> bool:
    try:
        return _ph.verify(hash_guardado, token)
    except VerifyMismatchError:
        return False


# ─── Demo: Resistencia a Rainbow Tables ────────────────────────────────────

def demo_rainbow_resistance():
    """
    Demuestra que el mismo input produce hashes distintos (salt aleatorio).
    Ejecutar con: python -c "from conversion.crypto_utils import demo_rainbow_resistance; demo_rainbow_resistance()"
    """
    token = "sesion_test_123"
    h1 = hashear_token(token)
    h2 = hashear_token(token)
    h3 = hashear_token(token)

    print("=== Demo Resistencia Rainbow Tables ===")
    print(f"Mismo token '{token}' produce hashes DISTINTOS:")
    print(f"Hash 1: {h1[:60]}...")
    print(f"Hash 2: {h2[:60]}...")
    print(f"Hash 3: {h3[:60]}...")
    print(f"\n¿h1 == h2? {h1 == h2}")  # False
    print(f"¿h1 verifica contra token? {verificar_token(token, h1)}")  # True
    print("\n✅ Rainbow Tables son inútiles: cada hash tiene un salt único embebido")
