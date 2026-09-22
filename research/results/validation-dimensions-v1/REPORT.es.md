# Piloto exploratorio: resultados reproducibles

**No es un paper terminado ni una demostración de novedad.**
Protocolo: [protocol.md](protocol.md). Configuración: [config.json](config.json).
Diseño: `paired-noise-v1`. Código: `e5d5f039826de3fc8398ed35de79285c3deacbee`;
árbol modificado al ejecutar: `True`.

## Ejecución y alcance

- 1050 datasets; 16800 ajustes;
  6300 decisiones de selección de k.
- 50 familias independientes, emparejadas entre condiciones.
- 0 ajustes no válidos;
  0 selecciones no válidas;
  0 ajustes con avisos.
- Tiempo total de ejecución: 233.5 segundos, un hilo.
- 4 grupos gaussianos equilibrados, 4 coordenadas
  de señal y 100 observaciones por grupo. No generalizar a otras geometrías.

![Galería predeterminada](figures/gallery.png)

## Recuperación con el número real de grupos proporcionado

ARI=1 indica coincidencia perfecta con las etiquetas generadoras. Cada media
resume familias independientes; los intervalos t son puntuales y exploratorios.
`n` es el número de ajustes válidos, no el número de observaciones del dataset.

Sin ruido añadido:

| std | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- |
| 0.050 | raw | kmeans | 1.000 | 1.000 | 1.000 | 50 |
| 0.050 | raw | ward | 1.000 | 1.000 | 1.000 | 50 |
| 0.050 | standardized | kmeans | 1.000 | 1.000 | 1.000 | 50 |
| 0.050 | standardized | ward | 0.989 | 0.979 | 0.999 | 50 |
| 0.150 | raw | kmeans | 0.879 | 0.862 | 0.897 | 50 |
| 0.150 | raw | ward | 0.799 | 0.775 | 0.823 | 50 |
| 0.150 | standardized | kmeans | 0.832 | 0.791 | 0.872 | 50 |
| 0.150 | standardized | ward | 0.756 | 0.713 | 0.798 | 50 |
| 0.300 | raw | kmeans | 0.389 | 0.366 | 0.412 | 50 |
| 0.300 | raw | ward | 0.268 | 0.248 | 0.289 | 50 |
| 0.300 | standardized | kmeans | 0.361 | 0.330 | 0.392 | 50 |
| 0.300 | standardized | ward | 0.266 | 0.244 | 0.288 | 50 |

Con 32 variables irrelevantes:

| std | distribution | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | kmeans | 0.342 | 0.279 | 0.404 | 50 |
| 0.050 | normal | raw | ward | 0.156 | 0.130 | 0.182 | 50 |
| 0.050 | normal | standardized | kmeans | 0.639 | 0.576 | 0.703 | 50 |
| 0.050 | normal | standardized | ward | 0.383 | 0.344 | 0.422 | 50 |
| 0.050 | uniform | raw | kmeans | 0.345 | 0.282 | 0.408 | 50 |
| 0.050 | uniform | raw | ward | 0.135 | 0.110 | 0.160 | 50 |
| 0.050 | uniform | standardized | kmeans | 0.642 | 0.581 | 0.703 | 50 |
| 0.050 | uniform | standardized | ward | 0.369 | 0.331 | 0.406 | 50 |
| 0.150 | normal | raw | kmeans | 0.338 | 0.288 | 0.388 | 50 |
| 0.150 | normal | raw | ward | 0.147 | 0.125 | 0.168 | 50 |
| 0.150 | normal | standardized | kmeans | 0.391 | 0.343 | 0.440 | 50 |
| 0.150 | normal | standardized | ward | 0.184 | 0.161 | 0.206 | 50 |
| 0.150 | uniform | raw | kmeans | 0.317 | 0.267 | 0.367 | 50 |
| 0.150 | uniform | raw | ward | 0.131 | 0.112 | 0.149 | 50 |
| 0.150 | uniform | standardized | kmeans | 0.400 | 0.348 | 0.453 | 50 |
| 0.150 | uniform | standardized | ward | 0.175 | 0.155 | 0.195 | 50 |
| 0.300 | normal | raw | kmeans | 0.287 | 0.263 | 0.312 | 50 |
| 0.300 | normal | raw | ward | 0.128 | 0.114 | 0.142 | 50 |
| 0.300 | normal | standardized | kmeans | 0.091 | 0.076 | 0.105 | 50 |
| 0.300 | normal | standardized | ward | 0.041 | 0.035 | 0.047 | 50 |
| 0.300 | uniform | raw | kmeans | 0.284 | 0.258 | 0.310 | 50 |
| 0.300 | uniform | raw | ward | 0.130 | 0.117 | 0.144 | 50 |
| 0.300 | uniform | standardized | kmeans | 0.077 | 0.064 | 0.089 | 50 |
| 0.300 | uniform | standardized | ward | 0.039 | 0.031 | 0.047 | 50 |

![Recuperación](figures/recovery.png)

Los efectos emparejados ARI(q)-ARI(0) están en [paired_summary.csv](paired_summary.csv).
El contraste normal-uniforme está en [distribution_contrasts.csv](distribution_contrasts.csv).
Los niveles comparten observaciones y no son réplicas independientes adicionales.

## Selección de k sin consultar las etiquetas

Proporción de selecciones que recuperan el k generador, con el máximo ruido:
intervalos Wilson sobre todos los intentos; un fallo de selección no cuenta como éxito.

| std | distribution | preprocessing | criterion | proportion | ci_low | ci_high | valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | raw | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.050 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | standardized | davies_bouldin | 0.040 | 0.011 | 0.135 | 50 |
| 0.050 | normal | standardized | silhouette | 0.060 | 0.021 | 0.162 | 50 |
| 0.050 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | silhouette | 0.100 | 0.043 | 0.214 | 50 |
| 0.150 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.300 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | standardized | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | uniform | standardized | silhouette | 0.000 | 0.000 | 0.071 | 50 |

Resultados para todos los niveles: [k_recovery.csv](k_recovery.csv).
Pérdida de ARI respecto a la mejor partición candidata (referencia oráculo, no
procedimiento utilizable): [selection_summary.csv](selection_summary.csv).

## Diagnóstico: las etiquetas no cambian, la geometría sí

![Silhouette de etiquetas generadoras](figures/truth_silhouette.png)

Esta figura calcula Silhouette con las etiquetas generadoras fijas. Una variación
no representa una reclasificación. Por sí sola tampoco demuestra que un índice
sea incorrecto: describe una geometría diferente al incluir dimensiones irrelevantes.
Con solapamiento, recuperar componentes generadores y encontrar una partición
geométricamente preferida son objetivos distintos.

## Interpretación y próximos pasos

Este piloto comprueba viabilidad y estima variabilidad. No compara la superioridad
del generador frente a otros, ni establece recomendaciones generales de algoritmos.
Hay un antecedente cercano sobre ruido y métricas (McCrory y Thomas, 2024);
la novedad de una eventual contribución permanece por demostrar.

Antes de ampliar: revisar fallos y emparejamiento, evaluar los tamaños de efecto
por condición, completar la revisión de literatura y congelar otro protocolo con
semillas independientes. Añadir dimensiones requiere controlar la separación.
Ampliar algoritmos, geometrías y tamaños muestrales será una fase posterior.

## Auditoría

Datos de ajustes: [fits.csv](fits.csv); selección: [selections.csv](selections.csv);
diagnósticos por dataset: [datasets.jsonl](datasets.jsonl); metadatos y hashes:
[manifest.json](manifest.json). La galería exporta la réplica 0 para todas las
dispersiones, sin ruido y con el máximo ruido; no se seleccionaron ejemplos por resultados.
PDF de las figuras disponible junto a cada PNG.
