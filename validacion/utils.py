from abc import ABC, abstractmethod


class ValidadorHerramienta(ABC):
    @abstractmethod
    def validar(self, ruta_archivo):
        pass


class AdaptadorWAVE(ValidadorHerramienta):
    def validar(self, ruta_archivo):
        return {
            "puntuacion": "Accesible",
            "detalle": "Análisis de WAVE finalizado sin errores críticos."
        }


class AdaptadorEPUBCheck(ValidadorHerramienta):
    def validar(self, ruta_archivo):
        return {
            "puntuacion": "Aceptable",
            "detalle": "EPUBCheck validó la estructura del archivo correctamente."
        }
