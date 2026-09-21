# Random Clusters Generator

**Genera datos sintéticos reproducibles para investigar algoritmos de clustering.**
Indicas cuántos grupos, observaciones y variables quieres. Obtienes un CSV con las
etiquetas reales y un JSON que describe cómo se generó.

[English / documentación completa](README.md)

```text
ENTRADA                         PROCESO                       SALIDA
4 grupos                        Elegir centros distintos      demo.csv
100 observaciones por grupo  →  Generar puntos gaussianos  →   400 filas × 5 columnas
2 variables + 2 de ruido        Añadir ruido uniforme         s0,s1,d0,d1,cluster
desviación=0.05, semilla=42      Mezclar las filas              demo.json
                                                              parámetros, centros y semilla
```

## 1. Instala la herramienta

Necesitas **Python 3.10 o superior** y Git. En una terminal:

```bash
git clone https://github.com/josemarialuna/RandomClustersGenerator.git
cd RandomClustersGenerator
python -m venv .venv
```

Activa el entorno con el comando correspondiente:

| Terminal | Comando |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Después:

```bash
python -m pip install .
random-clusters --help
```

Si tu sistema utiliza `python3`, úsalo para crear el entorno. Si PowerShell impide
activarlo, puedes instalar con `.venv\Scripts\python.exe -m pip install .` y
ejecutar con `.venv\Scripts\python.exe -m random_clusters ...`.

## 2. Genera tu primer dataset

Copia esta línea completa:

```bash
random-clusters generate --clusters 4 --samples 100 --features 2 --noise 2 --std 0.05 --seed 42 --output data/demo.csv
```

| Parámetro | Qué significa |
| --- | --- |
| `--clusters 4` | Cuatro grupos |
| `--samples 100` | Cien observaciones **por grupo**, 400 en total |
| `--features 2` | Dos coordenadas gaussianas: `s0`, `s1` |
| `--noise 2` | Dos variables de ruido: `d0`, `d1` |
| `--std 0.05` | Desviación típica dentro de cada grupo |
| `--seed 42` | Semilla para repetir el experimento |
| `--output data/demo.csv` | Destino del resultado |

Se crean automáticamente la carpeta y estos dos archivos:

```text
data/
├── demo.csv     # datos: 400 filas y 5 columnas
└── demo.json    # parámetros, semilla, centros, versiones y hash del CSV
```

**Filas = grupos × observaciones por grupo.**
**Columnas = variables gaussianas + variables de ruido + etiqueta.**

El comando protege los archivos existentes. Elige otro nombre o añade
`--overwrite` si quieres reemplazarlos. Puedes usar `--noise 0`, `--no-labels`
para omitir la etiqueta o `--ordered` para dejar las filas agrupadas por clúster.
Si omites la semilla, se genera una y se guarda en el JSON.

## 3. Mira qué contiene

| Columnas | Contenido |
| --- | --- |
| `s0`, `s1` | Muestras normales alrededor de los centros de cada grupo |
| `d0`, `d1` | Ruido uniforme independiente entre 0 incluido y 1 excluido |
| `cluster` | Grupo real: 0, 1, 2 o 3 |

Para ver un caso mínimo sin dispersión ni ruido:

```bash
random-clusters generate --clusters 2 --samples 2 --features 1 --noise 0 --std 0 --seed 42 --ordered --output data/tiny.csv
```

Genera cuatro filas: dos observaciones por cada uno de los centros `0.25` y `0.75`.

```csv
s0,cluster
0.75,0
0.75,0
0.25,1
0.25,1
```

Puedes abrir el [CSV real de ejemplo](examples/tiny.csv) y su
[JSON de metadatos](examples/tiny.json) directamente en GitHub.

## 4. Utilízalo en tu investigación

```python
import pandas as pd

datos = pd.read_csv("data/demo.csv")
X = datos.drop(columns="cluster")  # variables de entrada: 400 × 4
y_real = datos["cluster"]  # etiquetas reales para evaluar

print(datos.head())
print(y_real.value_counts().sort_index())
```

**No incluyas `cluster` entre las variables de entrada del algoritmo.**
Sirve para comparar los grupos descubiertos con los grupos reales.

## 5. Genera varios experimentos

La entrada [examples/experiments.csv](examples/experiments.csv) contiene:

```csv
clusters,samples,features,noise,std,seed
4,100,2,2,0.05,42
4,100,2,8,0.05,42
6,100,3,2,0.10,123
```

Ejecuta:

```bash
random-clusters batch examples/experiments.csv --output data/experiments
```

| Fila de entrada | Salida | Tamaño con etiqueta |
| --- | --- | --- |
| 1 | `dataset_001.csv` y `.json` | 400 × 5 |
| 2 | `dataset_002.csv` y `.json` | 400 × 11 |
| 3 | `dataset_003.csv` y `.json` | 600 × 6 |

Modifica o añade filas para definir tus experimentos. Los seis campos son
obligatorios; se admiten comas o punto y coma. Se validan todas las filas antes de
generar datos. Para réplicas independientes, cambia la semilla.

## 6. Entiende cómo se generan los grupos

Cada centro es una combinación de coordenadas `0.25` y `0.75`. Con dos variables
hay cuatro centros posibles:

```text
         s1
  0.75    ● (0.25, 0.75)       ● (0.75, 0.75)

  0.25    ● (0.25, 0.25)       ● (0.75, 0.25)
         0.25                 0.75             s0
```

Se eligen centros distintos al azar y se generan muestras normales a su alrededor.
El máximo es **2 elevado al número de variables**, no el número de variables al
cuadrado. Se rechazan las configuraciones que superan ese máximo.

Todos los grupos tienen el mismo tamaño y varianza, y sus coordenadas son
independientes dentro de cada grupo. Una desviación mayor produce más dispersión
y puede hacer que se solapen. Las muestras normales no se recortan a `[0, 1]`.

Una coordenada gaussiana puede tener la misma media en todos los centros elegidos;
el campo `varying_signal_features` del JSON indica cuáles varían realmente entre
grupos. No se generan formas arbitrarias, outliers ni variables categóricas.

## 7. Repite un experimento

Guarda el CSV, el JSON, la revisión del repositorio y las dependencias instaladas:

```bash
git rev-parse HEAD
python -m pip freeze > environment.txt
```

Conservando las mismas versiones, puedes regenerar los datos desde el JSON:

```python
import json
from pathlib import Path
from random_clusters import GeneratorConfig, generate
from random_clusters.io import save_dataset

metadatos = json.loads(Path("data/demo.json").read_text(encoding="utf-8"))
resultado = generate(GeneratorConfig(**metadatos["parameters"]))
save_dataset(resultado, Path("data/repetido.csv"))
```

La semilla por sí sola no garantiza igualdad entre versiones distintas. El JSON
registra versiones, centros y un hash SHA-256 para comprobar la integridad del CSV.

## Añadir ruido a un dataset existente

```bash
random-clusters add-noise data/demo.csv --count 3 --seed 42 --output data/demo_extra.csv
```

Añade tres columnas nuevas sin sustituir las anteriores, conserva el orden de
filas y escribe otros archivos. El ruido es uniforme; para ruido normal usa
`--distribution normal --mean 1 --std 0.05`. Entrada y salida deben ser diferentes.
Se espera un CSV numérico con cabecera y separado por comas; pandas infiere los
tipos y no conserva el formato textual original.

## Si utilizabas la versión anterior

Los cuatro scripts se han sustituido por un paquete y tres subcomandos. Ya no hace
falta editar código ni generar una cuadrícula fija de cientos de configuraciones.
Para adaptar los CSV antiguos, cambia `clusters_num` por `clusters`,
`significant_num` por `features`, `dummy_num` por `noise` y `standard_dev` por `std`;
añade `samples` y `seed` y corrige las configuraciones que superen `2**features`.

**El comportamiento científico ha cambiado:** se eligen centros de todo el espacio
binario, se mezclan las filas por defecto y se usa un generador PCG64 con semilla.
Para reproducir experimentos históricos, conserva el código de aquella revisión.

El [piloto de investigación](research/README.md) incluye protocolo, antecedentes
y experimentos reproducibles sobre variables irrelevantes y selección de grupos.

Consulta la [documentación completa](README.md) para la API, desarrollo y pruebas.
Licencia [MIT](LICENSE). Autor: José María Luna-Romera. Si lo utilizas en un trabajo,
indica el repositorio, la revisión empleada, los parámetros y las semillas.
