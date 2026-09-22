# Piloto exploratorio: resultados reproducibles

**No es un paper terminado ni una demostración de novedad.**
Protocolo: [protocol.md](protocol.md). Configuración: [config.json](config.json).
Diseño: `paired-noise-v1`. Código: `ec319056cc03f4c5ced0b3deb99d598dc8afd6c5`;
árbol modificado al ejecutar: `False`.

## Ejecución y alcance

- 600 datasets; 9600 ajustes;
  3600 decisiones de selección de k.
- 200 familias independientes, emparejadas entre condiciones.
- 0 ajustes no válidos;
  0 selecciones no válidas;
  0 ajustes con avisos.
- Tiempo total de ejecución: 117.1 segundos, un hilo.
- 4 grupos gaussianos equilibrados, 2 coordenadas
  de señal y 100 observaciones por grupo. No generalizar a otras geometrías.

![Galería predeterminada](figures/gallery.png)

## Recuperación con el número real de grupos proporcionado

ARI=1 indica coincidencia perfecta con las etiquetas generadoras. Cada media
resume familias independientes; los intervalos t son puntuales y exploratorios.
`n` es el número de ajustes válidos, no el número de observaciones del dataset.

Sin ruido añadido:

| std | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- |
| 0.050 | raw | kmeans | 1.000 | 1.000 | 1.000 | 200 |
| 0.050 | raw | ward | 1.000 | 1.000 | 1.000 | 200 |
| 0.050 | standardized | kmeans | 1.000 | 1.000 | 1.000 | 200 |
| 0.050 | standardized | ward | 1.000 | 1.000 | 1.000 | 200 |

Con 2 variables irrelevantes:

| std | distribution | preprocessing | method | mean | ci_low | ci_high | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | kmeans | 0.630 | 0.595 | 0.666 | 200 |
| 0.050 | normal | raw | ward | 0.657 | 0.628 | 0.685 | 200 |
| 0.050 | normal | standardized | kmeans | 1.000 | 1.000 | 1.000 | 200 |
| 0.050 | normal | standardized | ward | 0.929 | 0.919 | 0.940 | 200 |
| 0.050 | uniform | raw | kmeans | 0.264 | 0.241 | 0.287 | 200 |
| 0.050 | uniform | raw | ward | 0.417 | 0.391 | 0.444 | 200 |
| 0.050 | uniform | standardized | kmeans | 0.947 | 0.930 | 0.963 | 200 |
| 0.050 | uniform | standardized | ward | 0.894 | 0.874 | 0.915 | 200 |

![Recuperación](figures/recovery.png)

Los efectos emparejados ARI(q)-ARI(0) están en [paired_summary.csv](paired_summary.csv).
El contraste normal-uniforme está en [distribution_contrasts.csv](distribution_contrasts.csv).
Los niveles comparten observaciones y no son réplicas independientes adicionales.

## Selección de k sin consultar las etiquetas

Proporción de selecciones que recuperan el k generador, con el máximo ruido:
intervalos Wilson sobre todos los intentos; un fallo de selección no cuenta como éxito.

| std | distribution | preprocessing | criterion | proportion | ci_low | ci_high | valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | normal | raw | calinski_harabasz | 0.010 | 0.003 | 0.036 | 200 |
| 0.050 | normal | raw | davies_bouldin | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | normal | raw | silhouette | 0.070 | 0.042 | 0.114 | 200 |
| 0.050 | normal | standardized | calinski_harabasz | 0.005 | 0.001 | 0.028 | 200 |
| 0.050 | normal | standardized | davies_bouldin | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | normal | standardized | silhouette | 0.935 | 0.892 | 0.962 | 200 |
| 0.050 | uniform | raw | calinski_harabasz | 0.005 | 0.001 | 0.028 | 200 |
| 0.050 | uniform | raw | davies_bouldin | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | uniform | raw | silhouette | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | uniform | standardized | calinski_harabasz | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | uniform | standardized | davies_bouldin | 0.000 | 0.000 | 0.019 | 200 |
| 0.050 | uniform | standardized | silhouette | 0.025 | 0.011 | 0.057 | 200 |

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
