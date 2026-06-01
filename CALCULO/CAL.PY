print ("HOLAMUNDO")  
 Tabla de Diferencias finitas
# resultado en: [título,tabla]
# Tarea: verificar tamaño de vectores
import numpy as np

# INGRESO, Datos de prueba
xi = np.array([0.10, 0.2, 0.3, 0.4])
fi = np.array([1.45, 1.6, 1.7, 2.0])

# PROCEDIMIENTO

# Tabla de Diferencias Finitas
titulo = ['i','xi','fi']
n  = len(xi)
ki = np.arange(0,n,1)
tabla = np.concatenate(([ki],[xi],[fi]),axis=0)
tabla = np.transpose(tabla)

# diferencias finitas vacia
dfinita = np.zeros(shape=(n,n),dtype=float)
tabla   = np.concatenate((tabla,dfinita), axis=1)

# Calcula tabla, inicia en columna 3
[n,m] = np.shape(tabla)
diagonal = n-1
j = 3
while (j < m):
    # Añade título para cada columna
    titulo.append('df'+str(j-2))

    # cada fila de columna
    i = 0
    while (i < diagonal):
        tabla[i,j] = tabla[i+1,j-1]-tabla[i,j-1]
        i = i + 1

    diagonal = diagonal - 1
    j = j + 1

# SALIDA
print('Tabla Diferencia Finita: ')
print([titulo])
print(tabla)
el resultado de aplicar el algoritmo es: Tabla de Diferencias finitas
# resultado en: [título,tabla]
# Tarea: verificar tamaño de vectores
import numpy as np

# INGRESO, Datos de prueba
xi = np.array([0.10, 0.2, 0.3, 0.4])
fi = np.array([1.45, 1.6, 1.7, 2.0])

# PROCEDIMIENTO

# Tabla de Diferencias Finitas
titulo = ['i','xi','fi']
n  = len(xi)
ki = np.arange(0,n,1)
tabla = np.concatenate(([ki],[xi],[fi]),axis=0)
tabla = np.transpose(tabla)

# diferencias finitas vacia
dfinita = np.zeros(shape=(n,n),dtype=float)
tabla   = np.concatenate((tabla,dfinita), axis=1)

# Calcula tabla, inicia en columna 3
[n,m] = np.shape(tabla)
diagonal = n-1
j = 3
while (j < m):
    # Añade título para cada columna
    titulo.append('df'+str(j-2))

    # cada fila de columna
    i = 0
    while (i < diagonal):
        tabla[i,j] = tabla[i+1,j-1]-tabla[i,j-1]
        i = i + 1

    diagonal = diagonal - 1
    j = j + 1

# SALIDA
print('Tabla Diferencia Finita: ')
print([titulo])
print(tabla)
el resultado de aplicar el algoritmo es:

Tabla Diferencia Finita: 
[['i', 'xi', 'fi', 'df1', 'df2', 'df3', 'df4']]
[[ 0.    0.1   1.45  0.15 -0.05  0.25  0.  ]
 [ 1.    0.2   1.6   0.1   0.2   0.    0.  ]
 [ 2.    0.3   1.7   0.3   0.    0.    0.  ]
 [ 3.    0.4   2.    0.    0.    0.    0.  ]]

>>> 
Gráfica de puntos con líneas horizontales
Para tener una referencia visual sobre las primeras diferencias finitas, en una gráfica se trazan las líneas horizontales que pasan por cada punto. Para las segundas diferencias se debe graficar las primeras diferencias finitas vs xi repitiendo el proceso. Las líneas de distancia se añadieron con un editor de imágenes.

las intrucciones adicionales al algoritmo anterior para añadir la gráfica son:

# Gráfica
import matplotlib.pyplot as plt

for i in range(0,n,1):
    plt.axhline(fi[i],ls='--', color='yellow')

plt.plot(xi,fi,'o', label = 'Puntos')

plt.legend()
plt.xlabel('xi')
plt.ylabel('fi')
plt.title('Diferencia Finita')
plt.show()

Tabla Diferencia Finita: 
[['i', 'xi', 'fi', 'df1', 'df2', 'df3', 'df4']]
[[ 0.    0.1   1.45  0.15 -0.05  0.25  0.  ]
 [ 1.    0.2   1.6   0.1   0.2   0.    0.  ]
 [ 2.    0.3   1.7   0.3   0.    0.    0.  ]
 [ 3.    0.4   2.    0.    0.    0.    0.  ]]

>>> 
Gráfica de puntos con líneas horizontales
Para tener una referencia visual sobre las primeras diferencias finitas, en una gráfica se trazan las líneas horizontales que pasan por cada punto. Para las segundas diferencias se debe graficar las primeras diferencias finitas vs xi repitiendo el proceso. Las líneas de distancia se añadieron con un editor de imágenes.

las intrucciones adicionales al algoritmo anterior para añadir la gráfica son:

# Gráfica
import matplotlib.pyplot as plt

for i in range(0,n,1):
    plt.axhline(fi[i],ls='--', color='yellow')

plt.plot(xi,fi,'o', label = 'Puntos')

plt.legend()
plt.xlabel('xi')
plt.ylabel('fi')
plt.title('Diferencia Finita')
plt.show()