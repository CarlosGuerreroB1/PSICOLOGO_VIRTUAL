def funcion(x):
    # Define tu función aquí
    return x**2  # Ejemplo de una función cuadrática

def diferenciacion_hacia_atras(f, x, h=1e-5):
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
