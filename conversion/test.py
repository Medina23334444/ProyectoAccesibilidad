from conversion.security_utils import proteger_archivo, descifrar_archivo
import os

# 1. Crear un archivo de prueba
with open("prueba.txt", "w") as f:
    f.write("Este es un mensaje secreto de la tesis de Luis.")

# 2. Cifrarlo
archivo_cifrado = proteger_archivo("prueba.txt")

# 3. Intentar leer el archivo cifrado (Debe salir basura/ruido)
with open(archivo_cifrado, "rb") as f:
    print(f"Contenido cifrado: {f.read()[:50]}...")

# 4. Descifrarlo para ver que recuperamos el original
descifrar_archivo(archivo_cifrado, "resultado_final.txt")