import argparse


def crear_vector(n):
    return [1.0] * n


def suma_secuencial(vector):
    total = 0.0
    for valor in vector:
        total += valor
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, nargs="?", default=1_000_000)
    args = parser.parse_args()

    vector = crear_vector(args.n)
    resultado = suma_secuencial(vector)
    esperado = float(args.n)

    print(f"n={args.n}")
    print(f"suma={resultado}")
    print(f"esperado={esperado}")
    print(f"correcto={resultado == esperado}")
