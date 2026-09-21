# Investigación: primer piloto reproducible

Esta carpeta inicia el trabajo hacia una posible publicación. Contiene un
[protocolo previo al análisis](PROTOCOL.md), una [revisión inicial de antecedentes](RELATED_WORK.md)
y una [configuración ejecutable](pilot.json). No es un manuscrito listo para enviar.

El antecedente de McCrory y Thomas (2024) obliga a afinar la aportación: estudiar
ruido y métricas ya se ha hecho. Este piloto evalúa la viabilidad de experimentos
emparejados, ruido con varianza comparable y selección del número de grupos.

## Ejecutar desde la raíz del repositorio

```bash
python -m pip install -e ".[dev,research]"
python -m pytest
python -m random_clusters.research.run --config research/pilot.json --output data/research/pilot-v1
python -m random_clusters.research.report data/research/pilot-v1
```

El directorio de salida debe ser nuevo; una ejecución anterior nunca se sobrescribe.
La ejecución imprime progreso por réplica. Usa un hilo y procesa los datasets
secuencialmente. Para una repetición, utiliza otro directorio. El tiempo dependerá
del ordenador; una prueba reducida está cubierta por los tests.

## Qué entra y qué sale

```text
pilot.json + PROTOCOL.md
  → 20 familias independientes
  → mismos datos de señal con 0, 2, 8 o 32 variables irrelevantes
  → 420 datasets, 6.720 ajustes, 2.520 selecciones de k
  → resultados crudos + hashes + resúmenes + figuras PNG/PDF + informe
```

| Archivo | Contenido |
| --- | --- |
| `config.json`, `protocol.md` | Copias exactas de las entradas |
| `manifest.json` | Versiones, revisión, hashes, recuentos y estado de ejecución |
| `datasets.jsonl` | Centros, separación, diagnósticos y huellas de cada dataset |
| `fits.csv` | Cada ajuste, métricas, semilla, tiempo, avisos y errores |
| `selections.csv` | Selección de k por cada índice y evaluación posterior |
| `truth_scores.csv` | Índices calculados manteniendo las etiquetas generadoras |
| `paired_summary.csv` | Cambio de ARI frente al caso sin ruido, con incertidumbre |
| `distribution_contrasts.csv` | Diferencia emparejada normal-uniforme |
| `k_recovery.csv` | Frecuencia de recuperar k, con intervalos Wilson |
| `gallery/` | Nueve CSV predeterminados: réplica 0, tres dispersiones, sin ruido y con máximo ruido |
| `figures/` | Gráficos PNG y PDF regenerables |
| `REPORT.es.md` | Informe automático del piloto en español |

La huella de un dataset incluye forma y valores float64 little-endian; la huella
de etiquetas emplea la misma codificación. No es el hash de un archivo CSV.
`manifest.json` diferencia esos hashes de los hashes de archivos exportados.
La galería permite inspeccionar datos reales; los restantes datasets se regeneran
con configuración, revisión y versiones, sin almacenar copias redundantes.

## Interpretación

ARI con k verdadero y recuperación de k son experimentos distintos. Las etiquetas
se usan solo para evaluación y para el diagnóstico declarado como oráculo. Un
índice que baja al añadir ruido no es automáticamente incorrecto. Los intervalos
son exploratorios y puntuales; las comparaciones emparejadas utilizan familias,
no observaciones ni ajustes, como unidades independientes.

La API pública y sus resultados previos no cambian. El módulo opcional de
investigación utiliza flujos aleatorios separados, con versión de diseño propia.

## Siguiente decisión

Después del piloto: auditar invariantes y resultados; completar la revisión de
literatura; decidir si existe una contribución diferenciada; preparar el diseño
ampliado con otra semilla y objetivos de precisión. Quedan pendientes comparaciones
con otros generadores, otras geometrías, dimensiones y tamaños, y más algoritmos.
