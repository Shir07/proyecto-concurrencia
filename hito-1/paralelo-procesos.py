import multiprocessing
import time
from multiprocessing import RawArray, Lock


class GestorSumaParalela:
    

    def __init__(self, vector, cantidad_procesos, tamano_bloque):

        self.elementos_totales = len(vector)
        self.cantidad_procesos = cantidad_procesos
        self.tamano_bloque = tamano_bloque

        # Vector almacenado en memoria compartida.
        self.vector_compartido = RawArray("d", vector)
        self.indice_compartido = multiprocessing.Value("i", 0)
        self.cerrojo = Lock()

    def obtener_siguiente_bloque(self):
        """
        El cerrojo garantiza que solamente un proceso pueda
        modificar el índice compartido

        retorna una tupla o None si no queda nada

        """

        with self.cerrojo:
            if self.indice_compartido.value >= self.elementos_totales:
                return None

            inicio_bloque = self.indice_compartido.value

            fin_bloque = min(
                inicio_bloque + self.tamano_bloque,
                self.elementos_totales
            )

            self.indice_compartido.value = fin_bloque

            return inicio_bloque, fin_bloque

    def procesar_bloques(self, resultado_parcial):
        suma_proceso = 0.0

        while True:
            bloque = self.obtener_siguiente_bloque()

            if bloque is None:
                break

            inicio_bloque, fin_bloque = bloque

            for indice_elemento in range(inicio_bloque, fin_bloque):
                suma_proceso += self.vector_compartido[indice_elemento]

        resultado_parcial[multiprocessing.current_process()._identity[0] - 1] = (
            suma_proceso
        )
# Creacion de los procesos, ejecucion de la suma y medidion de tiempo en segundos 
    def ejecutar(self):
        """
        retorna la suma de todos los eleementos y el tiempo de ejecucion en segundos

        """

        resultado_parcial = RawArray(
            "d",
            self.cantidad_procesos
        )

        procesos = []

        tiempo_inicio = time.perf_counter()

        for _ in range(self.cantidad_procesos):
            proceso = multiprocessing.Process(
                target=self.procesar_bloques,
                args=(resultado_parcial,)
            )

            procesos.append(proceso)
            proceso.start()

        for proceso in procesos:
            proceso.join()

        resultado_total = sum(resultado_parcial)
        tiempo_fin = time.perf_counter()
        tiempo_ejecucion = tiempo_fin - tiempo_inicio
        return resultado_total, tiempo_ejecucion


if __name__ == "__main__":
    cantidad_elementos = 10_000_000
    cantidad_procesos = multiprocessing.cpu_count()
    tamano_bloque = 10_000

    # vector prueba.
    vector_prueba = [
        float(indice_elemento)
        for indice_elemento in range(1, cantidad_elementos + 1)
    ]

    # Crear el gestor de suma paralela
    gestor_suma = GestorSumaParalela(
        vector=vector_prueba,
        cantidad_procesos=cantidad_procesos,
        tamano_bloque=tamano_bloque
    )

    # Ejecutar la suma
    resultado, tiempo = gestor_suma.ejecutar()

    resultado_esperado = (
        cantidad_elementos * (cantidad_elementos + 1)
    ) / 2

    print(f"Elementos procesados: {cantidad_elementos:,}")
    print(f"Procesos utilizados: {cantidad_procesos}")
    print(f"Tamaño de bloque: {tamano_bloque:,}")
    print(f"Resultado obtenido: {resultado:,.0f}")
    print(f"Resultado esperado: {resultado_esperado:,.0f}")
    print(f"Resultado correcto: {resultado == resultado_esperado}")
    print(f"Tiempo de ejecución: {tiempo:.6f} segundos")
    
