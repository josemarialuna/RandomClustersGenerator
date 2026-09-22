# Piloto exploratorio: resultados reproducibles

**No es un paper terminado ni una demostración de novedad.**
Protocolo: [protocol.md](protocol.md). Configuración: [config.json](config.json).
Diseño: `paired-noise-v1`. Código: `e5d5f039826de3fc8398ed35de79285c3deacbee`;
árbol modificado al ejecutar: `True`.

## Ejecución y alcance

- 1050 datasets; 25200 ajustes;
  6300 decisiones de selección de k.
- 50 familias independientes, emparejadas entre condiciones.
- 0 ajustes no válidos;
  0 selecciones no válidas;
  0 ajustes con avisos.
- Tiempo total de ejecución: 5848.0 segundos, un hilo.
- 8 grupos gaussianos equilibrados, 3 coordenadas
  de señal y 50 observaciones por grupo. No generalizar a otras geometrías.

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
| 0.050 | standardized | ward | 1.000 | 1.000 | 1.000 | 50 |
| 0.150 | raw | kmeans | 0.703 | 0.694 | 0.713 | 50 |
| 0.150 | raw | ward | 0.583 | 0.571 | 0.595 | 50 |
| 0.150 | standardized | kmeans | 0.701 | 0.690 | 0.711 | 50 |
| 0.150 | standardized | ward | 0.587 | 0.575 | 0.598 | 50 |
| 0.300 | raw | kmeans | 0.176 | 0.171 | 0.182 | 50 |
| 0.300 | raw | ward | 0.154 | 0.149 | 0.160 | 50 |
| 0.300 | standardized | kmeans | 0.175 | 0.170 | 0.180 | 50 |
| 0.300 | standardized | ward | 0.157 | 0.152 | 0.163 | 50 |

Con 32 variables irrelevantes:

| std | distribution | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | kmeans | 0.027 | 0.024 | 0.030 | 50 |
| 0.050 | normal | raw | ward | 0.022 | 0.020 | 0.024 | 50 |
| 0.050 | normal | standardized | kmeans | 0.053 | 0.048 | 0.057 | 50 |
| 0.050 | normal | standardized | ward | 0.048 | 0.044 | 0.052 | 50 |
| 0.050 | uniform | raw | kmeans | 0.024 | 0.021 | 0.027 | 50 |
| 0.050 | uniform | raw | ward | 0.019 | 0.017 | 0.022 | 50 |
| 0.050 | uniform | standardized | kmeans | 0.052 | 0.046 | 0.057 | 50 |
| 0.050 | uniform | standardized | ward | 0.036 | 0.033 | 0.040 | 50 |
| 0.150 | normal | raw | kmeans | 0.040 | 0.037 | 0.044 | 50 |
| 0.150 | normal | raw | ward | 0.028 | 0.025 | 0.031 | 50 |
| 0.150 | normal | standardized | kmeans | 0.040 | 0.036 | 0.043 | 50 |
| 0.150 | normal | standardized | ward | 0.031 | 0.028 | 0.034 | 50 |
| 0.150 | uniform | raw | kmeans | 0.036 | 0.032 | 0.039 | 50 |
| 0.150 | uniform | raw | ward | 0.027 | 0.024 | 0.031 | 50 |
| 0.150 | uniform | standardized | kmeans | 0.035 | 0.031 | 0.039 | 50 |
| 0.150 | uniform | standardized | ward | 0.025 | 0.022 | 0.027 | 50 |
| 0.300 | normal | raw | kmeans | 0.083 | 0.079 | 0.087 | 50 |
| 0.300 | normal | raw | ward | 0.055 | 0.050 | 0.059 | 50 |
| 0.300 | normal | standardized | kmeans | 0.020 | 0.018 | 0.022 | 50 |
| 0.300 | normal | standardized | ward | 0.015 | 0.013 | 0.017 | 50 |
| 0.300 | uniform | raw | kmeans | 0.079 | 0.074 | 0.084 | 50 |
| 0.300 | uniform | raw | ward | 0.050 | 0.046 | 0.054 | 50 |
| 0.300 | uniform | standardized | kmeans | 0.017 | 0.016 | 0.019 | 50 |
| 0.300 | uniform | standardized | ward | 0.010 | 0.009 | 0.012 | 50 |

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
| 0.050 | normal | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | standardized | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.050 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | silhouette | 0.060 | 0.021 | 0.162 | 50 |
| 0.150 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | silhouette | 0.060 | 0.021 | 0.162 | 50 |
| 0.150 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | silhouette | 0.060 | 0.021 | 0.162 | 50 |
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
| 0.300 | uniform | standardized | silhouette | 0.060 | 0.021 | 0.162 | 50 |

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
