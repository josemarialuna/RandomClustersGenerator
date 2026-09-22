# Piloto exploratorio: resultados reproducibles

**No es un paper terminado ni una demostración de novedad.**
Protocolo: [protocol.md](protocol.md). Configuración: [config.json](config.json).
Diseño: `paired-noise-v1`. Código: `6c70699275a9cf967bf1436f0c366f7a98926cc5`;
árbol modificado al ejecutar: `True`.

## Ejecución y alcance

- 1050 datasets; 16800 ajustes;
  6300 decisiones de selección de k.
- 50 familias independientes, emparejadas entre condiciones.
- 0 ajustes no válidos;
  0 selecciones no válidas;
  0 ajustes con avisos.
- Tiempo total de ejecución: 183.4 segundos, un hilo.
- 4 grupos gaussianos equilibrados, 2 coordenadas
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
| 0.150 | raw | kmeans | 0.765 | 0.752 | 0.779 | 50 |
| 0.150 | raw | ward | 0.662 | 0.638 | 0.685 | 50 |
| 0.150 | standardized | kmeans | 0.766 | 0.752 | 0.780 | 50 |
| 0.150 | standardized | ward | 0.659 | 0.636 | 0.683 | 50 |
| 0.300 | raw | kmeans | 0.246 | 0.231 | 0.261 | 50 |
| 0.300 | raw | ward | 0.207 | 0.197 | 0.217 | 50 |
| 0.300 | standardized | kmeans | 0.245 | 0.230 | 0.260 | 50 |
| 0.300 | standardized | ward | 0.209 | 0.197 | 0.221 | 50 |

Con 32 variables irrelevantes:

| std | distribution | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | kmeans | 0.030 | 0.025 | 0.035 | 50 |
| 0.050 | normal | raw | ward | 0.020 | 0.015 | 0.026 | 50 |
| 0.050 | normal | standardized | kmeans | 0.048 | 0.039 | 0.057 | 50 |
| 0.050 | normal | standardized | ward | 0.041 | 0.035 | 0.048 | 50 |
| 0.050 | uniform | raw | kmeans | 0.030 | 0.024 | 0.036 | 50 |
| 0.050 | uniform | raw | ward | 0.017 | 0.013 | 0.021 | 50 |
| 0.050 | uniform | standardized | kmeans | 0.050 | 0.041 | 0.059 | 50 |
| 0.050 | uniform | standardized | ward | 0.034 | 0.027 | 0.041 | 50 |
| 0.150 | normal | raw | kmeans | 0.045 | 0.036 | 0.055 | 50 |
| 0.150 | normal | raw | ward | 0.029 | 0.023 | 0.035 | 50 |
| 0.150 | normal | standardized | kmeans | 0.041 | 0.033 | 0.049 | 50 |
| 0.150 | normal | standardized | ward | 0.033 | 0.027 | 0.039 | 50 |
| 0.150 | uniform | raw | kmeans | 0.039 | 0.031 | 0.046 | 50 |
| 0.150 | uniform | raw | ward | 0.027 | 0.021 | 0.032 | 50 |
| 0.150 | uniform | standardized | kmeans | 0.041 | 0.034 | 0.048 | 50 |
| 0.150 | uniform | standardized | ward | 0.025 | 0.019 | 0.030 | 50 |
| 0.300 | normal | raw | kmeans | 0.110 | 0.100 | 0.120 | 50 |
| 0.300 | normal | raw | ward | 0.063 | 0.056 | 0.070 | 50 |
| 0.300 | normal | standardized | kmeans | 0.021 | 0.016 | 0.026 | 50 |
| 0.300 | normal | standardized | ward | 0.018 | 0.013 | 0.023 | 50 |
| 0.300 | uniform | raw | kmeans | 0.100 | 0.089 | 0.111 | 50 |
| 0.300 | uniform | raw | ward | 0.063 | 0.057 | 0.070 | 50 |
| 0.300 | uniform | standardized | kmeans | 0.023 | 0.018 | 0.029 | 50 |
| 0.300 | uniform | standardized | ward | 0.016 | 0.012 | 0.020 | 50 |

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
| 0.050 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | normal | standardized | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.050 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | raw | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.050 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.050 | uniform | standardized | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.150 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | normal | standardized | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.150 | uniform | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | raw | silhouette | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.150 | uniform | standardized | silhouette | 0.020 | 0.004 | 0.105 | 50 |
| 0.300 | normal | raw | calinski_harabasz | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.071 | 50 |
| 0.300 | normal | raw | silhouette | 0.020 | 0.004 | 0.105 | 50 |
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
