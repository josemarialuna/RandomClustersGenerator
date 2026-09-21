"""Rebuild summaries and publication-size figures from the recorded pilot outputs."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import norm, t

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .run import sha256


def interval(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    n = len(values)
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, mcse=np.nan, ci_low=np.nan, ci_high=np.nan)
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if n > 1 else np.nan
    mcse = sd / np.sqrt(n)
    width = float(t.ppf(0.975, n - 1)) * mcse if n > 1 else np.nan
    return dict(n=n, mean=mean, sd=sd, mcse=mcse, ci_low=mean - width, ci_high=mean + width)


def wilson(successes, total):
    if total == 0:
        return np.nan, np.nan
    z = norm.ppf(0.975)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return float(center - half), float(center + half)


def summarize(frame, groups, metrics):
    rows = []
    for keys, group in frame.groupby(groups, dropna=False, sort=True):
        identity = dict(zip(groups, keys))
        for metric in metrics:
            rows.append(
                {
                    **identity,
                    "metric": metric,
                    "attempted": len(group),
                    **interval(group[metric].to_numpy()),
                }
            )
    return pd.DataFrame(rows)


def paired_differences(oracle):
    keys = ["replicate", "std", "preprocessing", "method"]
    baseline = oracle[oracle.noise == 0][keys + ["ari"]].rename(columns={"ari": "baseline_ari"})
    joined = oracle[oracle.noise > 0].merge(baseline, on=keys, validate="many_to_one")
    joined["ari_difference"] = joined.ari - joined.baseline_ari
    return joined


def distribution_differences(oracle):
    keys = ["replicate", "std", "noise", "preprocessing", "method"]
    uniform = oracle[oracle.distribution == "uniform"][keys + ["ari"]]
    normal = oracle[oracle.distribution == "normal"][keys + ["ari"]]
    joined = normal.merge(uniform, on=keys, suffixes=("_normal", "_uniform"), validate="one_to_one")
    joined["ari_difference"] = joined.ari_normal - joined.ari_uniform
    return joined


def line_figure(summary, path, *, metric, ylabel, by_method):
    stds = sorted(summary["std"].unique())
    preprocessings = list(summary.preprocessing.unique())
    fig, axes = plt.subplots(
        len(preprocessings),
        len(stds),
        squeeze=False,
        figsize=(4.0 * len(stds), 3.1 * len(preprocessings)),
    )
    colors = {"kmeans": "#087e8b", "ward": "#b44b15", "truth": "#087e8b"}
    for row, preprocessing in enumerate(preprocessings):
        for column, std in enumerate(stds):
            ax = axes[row, column]
            subset = summary[
                (summary["std"] == std)
                & (summary.preprocessing == preprocessing)
                & (summary.metric == metric)
            ]
            methods = list(subset.method.unique()) if by_method else ["truth"]
            for method in methods:
                method_rows = subset[subset.method == method] if by_method else subset
                baseline = method_rows[method_rows.noise == 0]
                distributions = sorted(set(method_rows.distribution) - {"none"})
                for distribution in distributions:
                    series = pd.concat(
                        [baseline, method_rows[method_rows.distribution == distribution]]
                    )
                    series = series.sort_values("noise")
                    label = f"{method}: {distribution}" if by_method else distribution
                    style = "-" if distribution == "uniform" else "--"
                    color = (
                        colors[method]
                        if by_method
                        else ("#087e8b" if distribution == "uniform" else "#b44b15")
                    )
                    ax.plot(
                        series.noise,
                        series["mean"],
                        style,
                        marker="o",
                        markersize=3,
                        color=color,
                        label=label,
                    )
                    ax.fill_between(
                        series.noise, series.ci_low, series.ci_high, color=color, alpha=0.09
                    )
            ax.set_title(f"σ = {std:g} · {preprocessing}")
            ax.set_xlabel("Added irrelevant dimensions")
            ax.set_ylabel(ylabel)
            ax.grid(alpha=0.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2 if by_method else 2, frameon=False)
    fig.suptitle("Exploratory pilot · means and pointwise 95% t intervals", fontsize=12)
    fig.tight_layout(rect=(0, 0.09, 1, 0.94))
    fig.savefig(path.with_suffix(".png"), dpi=180)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def gallery_figure(output, config, figures):
    stds = config["standard_deviations"]
    fig, axes = plt.subplots(1, len(stds), squeeze=False, figsize=(4 * len(stds), 3.6))
    for ax, std in zip(axes[0], stds):
        table = pd.read_csv(output / "gallery" / f"r000_sd{std:g}_q0_none.csv")
        if config["features"] < 2:
            ax.scatter(table.s0, np.zeros(len(table)), c=table.cluster, cmap="tab10", s=10)
        else:
            ax.scatter(table.s0, table.s1, c=table.cluster, cmap="tab10", s=10, alpha=0.65)
        ax.set(xlabel="s0", ylabel="s1" if config["features"] >= 2 else "", title=f"σ = {std:g}")
        ax.set_aspect("equal", adjustable="box")
    fig.suptitle("Predetermined replicate 0 · generating labels · signal coordinates only")
    fig.tight_layout()
    fig.savefig(figures / "gallery.png", dpi=180)
    fig.savefig(figures / "gallery.pdf")
    plt.close(fig)


def table_markdown(frame, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        values = [
            f"{row[name]:.3f}" if isinstance(row[name], (float, np.floating)) else str(row[name])
            for name in columns
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def report(output: Path):
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise ValueError("cannot report an incomplete run")
    for name, digest in manifest["output_sha256"].items():
        if sha256(output / name) != digest:
            raise ValueError(f"input integrity mismatch: {name}")
    config = manifest["config"]
    fits = pd.read_csv(output / "fits.csv")
    selections = pd.read_csv(output / "selections.csv")
    truth = pd.read_csv(output / "truth_scores.csv")
    oracle = fits[fits.candidate_k == config["clusters"]].copy()
    oracle.loc[
        oracle.status != "ok", ["ari", "nmi", "silhouette", "calinski_harabasz", "davies_bouldin"]
    ] = np.nan
    groups = ["std", "noise", "distribution", "preprocessing", "method"]
    summaries = summarize(
        oracle, groups, ["ari", "nmi", "silhouette", "calinski_harabasz", "davies_bouldin"]
    )
    differences = paired_differences(oracle)
    paired_summary = summarize(differences, groups, ["ari_difference"])
    contrast = distribution_differences(oracle)
    contrast_summary = summarize(
        contrast, ["std", "noise", "preprocessing", "method"], ["ari_difference"]
    )
    truth_summary = summarize(
        truth, groups[:-1], ["silhouette", "calinski_harabasz", "davies_bouldin"]
    )
    selections.loc[selections.status != "ok", ["ari", "nmi", "ari_regret"]] = np.nan
    selection_groups = ["std", "noise", "distribution", "preprocessing", "criterion"]
    selection_summary = summarize(selections, selection_groups, ["ari", "ari_regret"])
    success_rows = []
    for keys, group in selections.groupby(selection_groups, sort=True):
        successes = int(group.correct_k.fillna(0).sum())
        low, high = wilson(successes, len(group))
        success_rows.append(
            {
                **dict(zip(selection_groups, keys)),
                "attempted": len(group),
                "valid": int((group.status == "ok").sum()),
                "successes": successes,
                "proportion": successes / len(group),
                "ci_low": low,
                "ci_high": high,
            }
        )
    success = pd.DataFrame(success_rows)
    artifacts = {
        "oracle_summary.csv": summaries,
        "paired_ari.csv": differences,
        "paired_summary.csv": paired_summary,
        "distribution_contrasts.csv": contrast_summary,
        "truth_summary.csv": truth_summary,
        "selection_summary.csv": selection_summary,
        "k_recovery.csv": success,
        "fit_failures.csv": fits[fits.status != "ok"],
        "fit_warnings.csv": fits[fits.warnings.notna()],
    }
    for name, frame in artifacts.items():
        frame.to_csv(output / name, index=False, float_format="%.17g", lineterminator="\n")
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    line_figure(
        summaries, figures / "recovery", metric="ari", ylabel="Adjusted Rand index", by_method=True
    )
    line_figure(
        truth_summary,
        figures / "truth_silhouette",
        metric="silhouette",
        ylabel="Silhouette of fixed generating labels",
        by_method=False,
    )
    gallery_figure(output, config, figures)
    endpoint = summaries[
        (summaries.metric == "ari") & (summaries.noise == max(config["noise_counts"]))
    ]
    baseline = summaries[(summaries.metric == "ari") & (summaries.noise == 0)]
    selected_endpoint = success[success.noise == max(config["noise_counts"])]
    endpoint_table = table_markdown(
        endpoint,
        ["std", "distribution", "preprocessing", "method", "mean", "ci_low", "ci_high", "n"],
    )
    selection_table = table_markdown(
        selected_endpoint,
        [
            "std",
            "distribution",
            "preprocessing",
            "criterion",
            "proportion",
            "ci_low",
            "ci_high",
            "valid",
        ],
    )
    report_text = f"""# Piloto exploratorio: resultados reproducibles

**No es un paper terminado ni una demostración de novedad.**
Protocolo: [protocol.md](protocol.md). Configuración: [config.json](config.json).
Diseño: `{manifest["design_version"]}`. Código: `{manifest["source_commit"]}`;
árbol modificado al ejecutar: `{manifest["git_dirty"]}`.

## Ejecución y alcance

- {manifest["observed"]["datasets"]} datasets; {manifest["observed"]["fits"]} ajustes;
  {manifest["observed"]["selections"]} decisiones de selección de k.
- {config["replicates"]} familias independientes, emparejadas entre condiciones.
- {manifest["observed"]["fit_failures"]} ajustes no válidos;
  {manifest["observed"]["selection_failures"]} selecciones no válidas;
  {manifest["observed"]["fit_warnings"]} ajustes con avisos.
- Tiempo total de ejecución: {manifest["elapsed_seconds"]:.1f} segundos, un hilo.
- {config["clusters"]} grupos gaussianos equilibrados, {config["features"]} coordenadas
  de señal y {config["samples"]} observaciones por grupo. No generalizar a otras geometrías.

![Galería predeterminada](figures/gallery.png)

## Recuperación con el número real de grupos proporcionado

ARI=1 indica coincidencia perfecta con las etiquetas generadoras. Cada media
resume familias independientes; los intervalos t son puntuales y exploratorios.
`n` es el número de ajustes válidos, no el número de observaciones del dataset.

Sin ruido añadido:

{table_markdown(baseline, ["std", "preprocessing", "method", "mean", "ci_low", "ci_high", "n"])}

Con {max(config["noise_counts"])} variables irrelevantes:

{endpoint_table}

![Recuperación](figures/recovery.png)

Los efectos emparejados ARI(q)-ARI(0) están en [paired_summary.csv](paired_summary.csv).
El contraste normal-uniforme está en [distribution_contrasts.csv](distribution_contrasts.csv).
Los niveles comparten observaciones y no son réplicas independientes adicionales.

## Selección de k sin consultar las etiquetas

Proporción de selecciones que recuperan el k generador, con el máximo ruido:
intervalos Wilson sobre todos los intentos; un fallo de selección no cuenta como éxito.

{selection_table}

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
"""
    (output / "REPORT.es.md").write_text(report_text, encoding="utf-8", newline="\n")
    derived = list(artifacts) + ["REPORT.es.md"]
    derived += [
        str(path.relative_to(output)).replace("\\", "/") for path in sorted(figures.iterdir())
    ]
    (output / "analysis_manifest.json").write_text(
        json.dumps(
            {
                "source_manifest_sha256": sha256(manifest_path),
                "report_source_sha256": sha256(Path(__file__)),
                "artifacts": {
                    name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                    for name in derived
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Report: {output / 'REPORT.es.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        report(args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
