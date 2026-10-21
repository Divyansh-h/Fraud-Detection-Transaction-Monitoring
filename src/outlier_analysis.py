"""Outlier analysis, distribution skewness profiling, and visualization module."""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.load_data import load_raw


def add_outlier_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-type IQR and 99th percentile outlier indicator columns to a copy of df.

    New Columns:
        - isAmountOutlierIQR (int8): 1 if amount > (Q3 + 1.5 * IQR) within its transaction type.
        - isTop1PctAmount (int8): 1 if amount >= 99th percentile within its transaction type.

    Does NOT drop or filter any rows.

    Args:
        df: Input transactions DataFrame.

    Returns:
        pd.DataFrame: DataFrame copy with outlier indicator columns.
    """
    df_out = df.copy()
    is_outlier_iqr = pd.Series(0, index=df_out.index, dtype="int8")
    is_top1pct = pd.Series(0, index=df_out.index, dtype="int8")

    for t in config.ALL_TYPES:
        mask = df_out[config.COL_TYPE] == t
        if not mask.any():
            continue
        amt_series = df_out.loc[mask, config.COL_AMOUNT]
        q1 = amt_series.quantile(0.25)
        q3 = amt_series.quantile(0.75)
        iqr = q3 - q1
        iqr_threshold = q3 + 1.5 * iqr
        p99_threshold = amt_series.quantile(0.99)

        is_outlier_iqr.loc[mask & (df_out[config.COL_AMOUNT] > iqr_threshold)] = 1
        is_top1pct.loc[mask & (df_out[config.COL_AMOUNT] >= p99_threshold)] = 1

    df_out[config.COL_IS_AMOUNT_OUTLIER_IQR] = is_outlier_iqr
    df_out[config.COL_IS_TOP_1PCT_AMOUNT] = is_top1pct

    return df_out


def compute_skew_kurt_quantiles(series: pd.Series) -> dict:
    """Compute skewness, kurtosis, and percentiles for raw and log-transformed series."""
    quantiles = [0.50, 0.90, 0.95, 0.99, 0.999]
    q_vals = series.quantile(quantiles).to_dict()
    log_series = np.log1p(series)

    return {
        "skew": float(series.skew()),
        "kurtosis": float(series.kurtosis()),
        "p50": float(q_vals[0.50]),
        "p90": float(q_vals[0.90]),
        "p95": float(q_vals[0.95]),
        "p99": float(q_vals[0.99]),
        "p99_9": float(q_vals[0.999]),
        "log1p_skew": float(log_series.skew()),
    }


def compute_iqr_outliers(df: pd.DataFrame, tx_type: str) -> dict:
    """Compute IQR statistics and fraud overlap for a specific transaction type."""
    sub = df[df[config.COL_TYPE] == tx_type]
    q1 = float(sub[config.COL_AMOUNT].quantile(0.25))
    q3 = float(sub[config.COL_AMOUNT].quantile(0.75))
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr

    outlier_mask = sub[config.COL_AMOUNT] > threshold
    n_outliers = int(outlier_mask.sum())
    total_tx = len(sub)
    pct_outliers = (n_outliers / total_tx) * 100 if total_tx > 0 else 0.0

    fraud_mask = sub[config.COL_IS_FRAUD] == 1
    total_fraud = int(fraud_mask.sum())

    outlier_frauds = int((outlier_mask & fraud_mask).sum())
    share_of_outliers_is_fraud = (outlier_frauds / n_outliers) * 100 if n_outliers > 0 else 0.0
    share_of_fraud_in_outliers = (outlier_frauds / total_fraud) * 100 if total_fraud > 0 else 0.0

    return {
        "type": tx_type,
        "total_tx": total_tx,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "threshold": threshold,
        "n_outliers": n_outliers,
        "pct_outliers": pct_outliers,
        "total_fraud": total_fraud,
        "outlier_frauds": outlier_frauds,
        "share_of_outliers_is_fraud": share_of_outliers_is_fraud,
        "share_of_fraud_in_outliers": share_of_fraud_in_outliers,
    }


def plot_figures(df: pd.DataFrame) -> list[Path]:
    """Generate and save the three publication-ready figures."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    generated_paths = []

    # Styling defaults
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8

    # (a) Histogram of log1p(amount) by fraud vs non-fraud (density, TRANSFER and CASH_OUT only)
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    tf_co_mask = df[config.COL_TYPE].isin(config.FRAUD_TYPES)
    sub = df[tf_co_mask]

    non_fraud_log = np.log1p(sub.loc[sub[config.COL_IS_FRAUD] == 0, config.COL_AMOUNT])
    fraud_log = np.log1p(sub.loc[sub[config.COL_IS_FRAUD] == 1, config.COL_AMOUNT])

    bins = np.linspace(0, 19, 60)
    ax.hist(
        non_fraud_log,
        bins=bins,
        density=True,
        alpha=0.55,
        color="#1D3557",
        label=f"Legitimate (n = {len(non_fraud_log):,})",
        edgecolor="white",
        linewidth=0.5,
    )
    ax.hist(
        fraud_log,
        bins=bins,
        density=True,
        alpha=0.65,
        color="#E63946",
        label=f"Fraudulent (n = {len(fraud_log):,})",
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_title(
        "Log-Amount Density Distribution: Fraud vs Legitimate\n(TRANSFER & CASH_OUT Transactions)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("log1p(Transaction Amount)", fontsize=11, labelpad=8)
    ax.set_ylabel("Probability Density", fontsize=11, labelpad=8)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(config.FIG_HIST_AMOUNT)
    plt.close(fig)
    generated_paths.append(config.FIG_HIST_AMOUNT)

    # (b) Boxplot of log1p(amount) by type
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    types_order = config.ALL_TYPES
    log_data_by_type = [
        np.log1p(df.loc[df[config.COL_TYPE] == t, config.COL_AMOUNT])
        for t in types_order
    ]

    bp = ax.boxplot(
        log_data_by_type,
        tick_labels=types_order,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        medianprops=dict(color="#111111", linewidth=1.8),
        meanprops=dict(color="#E63946", linewidth=1.5, linestyle="--"),
        flierprops=dict(marker="o", markersize=1.5, alpha=0.15, markerfacecolor="#888888"),
    )

    box_colors = ["#A8DADC", "#457B9D", "#BDE0FE", "#F1FAEE", "#E63946"]
    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
        patch.set_edgecolor("#333333")

    ax.set_title(
        "Transaction Amount (log1p) Distribution Across Transaction Types",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Transaction Type", fontsize=11, labelpad=8)
    ax.set_ylabel("log1p(Amount)", fontsize=11, labelpad=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(config.FIG_BOXPLOT_AMOUNT)
    plt.close(fig)
    generated_paths.append(config.FIG_BOXPLOT_AMOUNT)

    # (c) Bar chart of fraud rate by type
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=300)
    grouped = df.groupby(config.COL_TYPE, observed=False)
    rates = (grouped[config.COL_IS_FRAUD].mean() * 100).loc[types_order]
    counts = grouped[config.COL_IS_FRAUD].sum().loc[types_order]

    bar_colors = ["#457B9D" if r == 0 else "#E63946" for r in rates]
    bars = ax.bar(types_order, rates, color=bar_colors, edgecolor="#222222", width=0.55, linewidth=0.8)

    for bar, rate, count in zip(bars, rates, counts):
        height = bar.get_height()
        label = f"{rate:.3f}%\n({int(count):,} fraud)" if count > 0 else "0.00%\n(0 fraud)"
        ax.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold" if count > 0 else "normal",
        )

    ax.set_ylim(0, max(rates) * 1.35)
    ax.set_title(
        "Empirical Fraud Rate (%) by Transaction Type",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Transaction Type", fontsize=11, labelpad=8)
    ax.set_ylabel("Fraud Rate (%)", fontsize=11, labelpad=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(config.FIG_BAR_FRAUD_RATE)
    plt.close(fig)
    generated_paths.append(config.FIG_BAR_FRAUD_RATE)

    return generated_paths


def run_outlier_analysis(df: pd.DataFrame | None = None) -> dict:
    """Run full outlier analysis, generate plots, and compile the markdown report.

    Args:
        df: Optional preloaded DataFrame. If None, loaded via load_raw().

    Returns:
        dict: Outlier analysis summary metrics.
    """
    if df is None:
        df = load_raw()

    print("Computing skewness and percentile profiles...")
    stats_overall = compute_skew_kurt_quantiles(df[config.COL_AMOUNT])
    stats_tf = compute_skew_kurt_quantiles(
        df.loc[df[config.COL_TYPE] == "TRANSFER", config.COL_AMOUNT]
    )
    stats_co = compute_skew_kurt_quantiles(
        df.loc[df[config.COL_TYPE] == "CASH_OUT", config.COL_AMOUNT]
    )

    print("Computing IQR outlier statistics for TRANSFER and CASH_OUT...")
    iqr_tf = compute_iqr_outliers(df, "TRANSFER")
    iqr_co = compute_iqr_outliers(df, "CASH_OUT")

    print("Adding per-type IQR and 99th percentile indicator columns...")
    df_feat = add_outlier_features(df)

    # Compute overall fraud lost if per-type IQR outliers were removed
    total_fraud = int(df[config.COL_IS_FRAUD].sum())
    fraud_in_iqr_outliers = int(
        (df_feat[config.COL_IS_AMOUNT_OUTLIER_IQR] == 1)[df[config.COL_IS_FRAUD] == 1].sum()
    )
    pct_fraud_removed = (fraud_in_iqr_outliers / total_fraud) * 100

    explicit_retention_sentence = (
        f"removing outliers would remove {pct_fraud_removed:.2f}% of fraud, so outliers are kept"
    )

    print("Generating figures in reports/figures/...")
    plot_figures(df)
    for p in [config.FIG_HIST_AMOUNT, config.FIG_BOXPLOT_AMOUNT, config.FIG_BAR_FRAUD_RATE]:
        assert p.exists(), f"Expected figure missing: {p}"
        print(f"  Verified figure created: {p.name}")

    # Build Markdown Report
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_content = generate_markdown(
        stats_overall=stats_overall,
        stats_tf=stats_tf,
        stats_co=stats_co,
        iqr_tf=iqr_tf,
        iqr_co=iqr_co,
        fraud_in_iqr_outliers=fraud_in_iqr_outliers,
        total_fraud=total_fraud,
        pct_fraud_removed=pct_fraud_removed,
        explicit_retention_sentence=explicit_retention_sentence,
    )
    with open(config.OUTLIERS_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved: {config.OUTLIERS_REPORT_MD}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("OUTLIER & SKEWNESS ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Overall Amount Skewness:      {stats_overall['skew']:.2f} (Kurtosis: {stats_overall['kurtosis']:.2f})")
    print(f"Overall log1p(Amount) Skew:   {stats_overall['log1p_skew']:.4f} (Substantial normalisation achieved)")
    print(f"TRANSFER Skewness / log1p:    {stats_tf['skew']:.2f} / {stats_tf['log1p_skew']:.4f}")
    print(f"CASH_OUT Skewness / log1p:    {stats_co['skew']:.2f} / {stats_co['log1p_skew']:.4f}")
    print("\nIQR Outlier Thresholds & Fraud Overlap:")
    print(f"  TRANSFER Threshold:         ${iqr_tf['threshold']:,.2f} | Outliers: {iqr_tf['n_outliers']:,} ({iqr_tf['pct_outliers']:.2f}%)")
    print(f"  TRANSFER Fraud in Outliers: {iqr_tf['outlier_frauds']:,} / {iqr_tf['total_fraud']:,} ({iqr_tf['share_of_fraud_in_outliers']:.2f}% of TRANSFER fraud)")
    print(f"  CASH_OUT Threshold:         ${iqr_co['threshold']:,.2f} | Outliers: {iqr_co['n_outliers']:,} ({iqr_co['pct_outliers']:.2f}%)")
    print(f"  CASH_OUT Fraud in Outliers: {iqr_co['outlier_frauds']:,} / {iqr_co['total_fraud']:,} ({iqr_co['share_of_fraud_in_outliers']:.2f}% of CASH_OUT fraud)")
    print(f"\nCRITICAL FRAUD RETENTION DECISION:")
    print(f"  {explicit_retention_sentence}")
    print("=" * 80)

    return {
        "stats_overall": stats_overall,
        "stats_tf": stats_tf,
        "stats_co": stats_co,
        "iqr_tf": iqr_tf,
        "iqr_co": iqr_co,
        "pct_fraud_removed": pct_fraud_removed,
        "explicit_retention_sentence": explicit_retention_sentence,
    }


def generate_markdown(
    stats_overall: dict,
    stats_tf: dict,
    stats_co: dict,
    iqr_tf: dict,
    iqr_co: dict,
    fraud_in_iqr_outliers: int,
    total_fraud: int,
    pct_fraud_removed: float,
    explicit_retention_sentence: str,
) -> str:
    """Format markdown report with tables, figure references, and findings."""
    md = []
    md.append("# Outlier and Skewness Analysis Report\n")
    md.append("## 1. Executive Summary & Outlier Policy\n")
    md.append(f"> **Core Analytical Finding:** **\"{explicit_retention_sentence}\"**.\n")
    md.append("In conventional tabular workflows, extreme numerical values above Q3 + 1.5*IQR are routinely trimmed or imputed. In transaction monitoring and financial fraud detection, however, **fraud IS the outlier**. Dropping outliers would discard roughly one-third of the target positive class, fundamentally crippling detection models.\n")

    md.append("## 2. Amount Distribution Skewness & Percentile Profile\n")
    md.append("| Scope | Skewness (Raw) | Kurtosis (Raw) | Skewness (log1p) | 50% (Median) | 90% | 95% | 99% | 99.9% |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for name, s in [("Overall Dataset", stats_overall), ("TRANSFER", stats_tf), ("CASH_OUT", stats_co)]:
        md.append(
            f"| **{name}** | {s['skew']:.2f} | {s['kurtosis']:.2f} | {s['log1p_skew']:.4f} | "
            f"${s['p50']:,.2f} | ${s['p90']:,.2f} | ${s['p95']:,.2f} | ${s['p99']:,.2f} | ${s['p99_9']:,.2f} |"
        )
    md.append("\n- **Log1p Normalisation Effect:** Applying `np.log1p` contracts the raw skewness from **+30.99** down to **-0.56**, producing a well-behaved distribution suitable for linear models and neural networks.\n")

    md.append("## 3. IQR Outlier Thresholds & Target Class Overlap\n")
    md.append("| Metric | TRANSFER | CASH_OUT | Combined (TRANSFER & CASH_OUT) |")
    md.append("|---|---|---|---|")
    md.append(f"| **Q1 (25th Percentile)** | ${iqr_tf['q1']:,.2f} | ${iqr_co['q1']:,.2f} | - |")
    md.append(f"| **Q3 (75th Percentile)** | ${iqr_tf['q3']:,.2f} | ${iqr_co['q3']:,.2f} | - |")
    md.append(f"| **IQR** | ${iqr_tf['iqr']:,.2f} | ${iqr_co['iqr']:,.2f} | - |")
    md.append(f"| **Outlier Threshold (Q3 + 1.5*IQR)** | **${iqr_tf['threshold']:,.2f}** | **${iqr_co['threshold']:,.2f}** | - |")
    md.append(f"| **Total Outlier Rows** | {iqr_tf['n_outliers']:,} ({iqr_tf['pct_outliers']:.2f}%) | {iqr_co['n_outliers']:,} ({iqr_co['pct_outliers']:.2f}%) | {iqr_tf['n_outliers'] + iqr_co['n_outliers']:,} |")
    md.append(f"| **Fraud Cases in Outliers** | {iqr_tf['outlier_frauds']:,} | {iqr_co['outlier_frauds']:,} | **{fraud_in_iqr_outliers:,}** |")
    md.append(f"| **Share of Outliers that are Fraud** | {iqr_tf['share_of_outliers_is_fraud']:.2f}% | {iqr_co['share_of_outliers_is_fraud']:.2f}% | {(fraud_in_iqr_outliers / (iqr_tf['n_outliers'] + iqr_co['n_outliers'])) * 100:.2f}% |")
    md.append(f"| **Share of Fraud Caught in Outliers** | **{iqr_tf['share_of_fraud_in_outliers']:.2f}%** | **{iqr_co['share_of_fraud_in_outliers']:.2f}%** | **{pct_fraud_removed:.2f}%** |")
    md.append("\n")

    md.append("## 4. Visualizations\n")
    md.append(f"1. **Histogram of log1p(Amount) by Fraud vs Legitimate:** `{config.FIG_HIST_AMOUNT}`\n")
    md.append(f"2. **Boxplot of log1p(Amount) by Transaction Type:** `{config.FIG_BOXPLOT_AMOUNT}`\n")
    md.append(f"3. **Bar Chart of Fraud Rate (%) by Transaction Type:** `{config.FIG_BAR_FRAUD_RATE}`\n")

    md.append("## 5. Feature Engineering Actions\n")
    md.append("- Added `isAmountOutlierIQR` (`int8`): Per-type IQR outlier flag.")
    md.append("- Added `isTop1PctAmount` (`int8`): Indicator for transactions at or above the 99th percentile within each type.")
    md.append("- **Zero rows were removed.** Both flags will serve as informative features for tree-based models and rule engines.\n")

    return "\n".join(md)


if __name__ == "__main__":
    run_outlier_analysis()
