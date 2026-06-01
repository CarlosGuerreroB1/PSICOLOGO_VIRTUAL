print("calcula la sigt funcion")
def funcion(x):
    return 3*x + 5

def diferenciacion_hacia_atras(f, x, h=0.1):
    """
    Calcula la derivada de la función f en el punto x usando diferenciación hacia atrás.
    """
    derivada_aproximada = (f(x) - f(x - h)) / h
    return derivada_aproximada

# Punto en el que deseas calcular la derivada
x = 2

# Calcula la derivada de la función en el punto dado
derivada = diferenciacion_hacia_atras(funcion, x)

# Imprime el resultado
print("La derivada en x =", x, "es aproximadamente", derivada)
