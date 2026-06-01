print("calcula la sigt funcion")
print("si tenemos los sigts datos si X0 =2 y h=0.1" )
def funcion(x):
    return 43*x - 21
def diferenciacion_hacia_atras(f, x, h=0.1):
    """
    Calcula la derivada de la función f en el punto x usando diferenciación hacia atrás.
    """
    derivada= (f(x) - f(x - h))
    div= derivada / h
    resultado = div
    return resultado
#Punto en el que se calcula la derivada 
x=4
resultado=diferenciacion_hacia_atras (funcion , x ,)
print ("El resultado de la funcion  cuando x =",x,"el resultado sera el sigt=", resultado)  


     