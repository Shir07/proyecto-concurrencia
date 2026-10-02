import threading


class GestorSumaParalela:
    def __init__(self, Vector, CantidadHilos, TamañoBloque):
        self.Vector = Vector
        self.ElementosTotales = len(Vector)
        self.CantidadHilos = CantidadHilos
        self.TamañoBloque = TamañoBloque
        self.IndiceCompartido = 0
        self.Cerrojo = threading.Lock()

    def SiguienteBloque(self):
        with self.Cerrojo:
            if self.IndiceCompartido >= self.ElementosTotales:
                return None

            InicioBloque = self.IndiceCompartido
            FinBloque = min(
                InicioBloque + self.TamañoBloque,
                self.ElementosTotales,
            )

            self.IndiceCompartido = FinBloque 
            return InicioBloque, FinBloque

    def ProcesarBloque(self, ResultadoParcial, IndiceHilo):
        SumaHilo = 0.0

        while True:
            Bloque = self.SiguienteBloque()

            if Bloque is None:
                break

            InicioBloque, FinBloque = Bloque

            for IndiceElemento in range(InicioBloque, FinBloque):
                SumaHilo += self.Vector[IndiceElemento]

        ResultadoParcial[IndiceHilo] = SumaHilo

    def ejecutar(self):
        ResultadoParcial = [0.0] * self.CantidadHilos
        Hilos = []

        for IndiceHilo in range(self.CantidadHilos):
            Hilo = threading.Thread(
                target=self.ProcesarBloque,
                args=(ResultadoParcial, IndiceHilo),
            )

            Hilos.append(Hilo)
            Hilo.start()

        for Hilo in Hilos:
            Hilo.join()

        return sum(ResultadoParcial)