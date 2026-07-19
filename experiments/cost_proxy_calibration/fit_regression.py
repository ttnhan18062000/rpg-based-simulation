"""Fit a linear regression of real token cost against cost_proxy_score's existing 3 features,
using experiments/cost_proxy_calibration/extracted_usage_features.jsonl (produced by
extract_transcript_usage.py). See PROPOSAL.md Section 4, steps 2-3.

Reports fit quality honestly (R^2, residual spread) and compares regression-derived weights
against the shipped W_BASH=0.001 / W_AGENT=50 / W_EDIT=1 constants in
tools/agent-monitoring/cost_proxy.py. Does NOT modify cost_proxy.py.
"""

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

HERE = Path(__file__).parent
IN_PATH = HERE / "extracted_usage_features.jsonl"

W_BASH_SHIPPED = 0.001
W_AGENT_SHIPPED = 50
W_EDIT_SHIPPED = 1


def load_rows() -> list[dict]:
    rows = []
    with open(IN_PATH, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def main() -> None:
    rows = load_rows()
    print(f"Loaded {len(rows)} rows from {IN_PATH.name}")

    # --- Full population (all turns with a usage block, including zero-tool-call turns) ---
    X_full = np.array([[r["bash_ms"], r["agent_count"], r["edit_count"]] for r in rows], dtype=float)
    y_full = np.array([r["total_tokens"] for r in rows], dtype=float)

    reg_full = LinearRegression()
    reg_full.fit(X_full, y_full)
    pred_full = reg_full.predict(X_full)
    r2_full = r2_score(y_full, pred_full)
    resid_full = y_full - pred_full

    print("\n=== Fit A: all assistant turns with a usage block (n={}) ===".format(len(rows)))
    print(f"  R^2: {r2_full:.4f}")
    print(f"  Intercept: {reg_full.intercept_:.2f}")
    print(f"  Coef bash_ms:     {reg_full.coef_[0]:.6f}  (shipped W_BASH={W_BASH_SHIPPED})")
    print(f"  Coef agent_count: {reg_full.coef_[1]:.4f}  (shipped W_AGENT={W_AGENT_SHIPPED})")
    print(f"  Coef edit_count:  {reg_full.coef_[2]:.4f}  (shipped W_EDIT={W_EDIT_SHIPPED})")
    print(f"  Residual std: {resid_full.std():.2f} tokens (target mean={y_full.mean():.1f}, std={y_full.std():.1f})")

    # --- Subset: only turns that actually made >=1 tool call (matches cost_proxy_score's own
    # scope — it only ever scores a group of real tool_rows, never a zero-tool-call turn) ---
    rows_tc = [r for r in rows if r["tool_call_count"] > 0]
    X_tc = np.array([[r["bash_ms"], r["agent_count"], r["edit_count"]] for r in rows_tc], dtype=float)
    y_tc = np.array([r["total_tokens"] for r in rows_tc], dtype=float)

    reg_tc = LinearRegression()
    reg_tc.fit(X_tc, y_tc)
    pred_tc = reg_tc.predict(X_tc)
    r2_tc = r2_score(y_tc, pred_tc)
    resid_tc = y_tc - pred_tc

    print("\n=== Fit B: only turns with >=1 tool_use block (n={}) ===".format(len(rows_tc)))
    print(f"  R^2: {r2_tc:.4f}")
    print(f"  Intercept: {reg_tc.intercept_:.2f}")
    print(f"  Coef bash_ms:     {reg_tc.coef_[0]:.6f}  (shipped W_BASH={W_BASH_SHIPPED})")
    print(f"  Coef agent_count: {reg_tc.coef_[1]:.4f}  (shipped W_AGENT={W_AGENT_SHIPPED})")
    print(f"  Coef edit_count:  {reg_tc.coef_[2]:.4f}  (shipped W_EDIT={W_EDIT_SHIPPED})")
    print(f"  Residual std: {resid_tc.std():.2f} tokens (target mean={y_tc.mean():.1f}, std={y_tc.std():.1f})")

    # --- Single-feature correlations, to see which feature (if any) carries the signal ---
    print("\n=== Single-feature Pearson correlations vs total_tokens (Fit B subset) ===")
    for i, name in enumerate(["bash_ms", "agent_count", "edit_count"]):
        col = X_tc[:, i]
        if col.std() == 0:
            print(f"  {name}: constant (no variance), correlation undefined")
            continue
        corr = np.corrcoef(col, y_tc)[0, 1]
        print(f"  {name}: r={corr:.4f}")

    # --- Feature summary stats, for context ---
    print("\n=== Feature summary (Fit B subset) ===")
    for i, name in enumerate(["bash_ms", "agent_count", "edit_count"]):
        col = X_tc[:, i]
        nz = (col > 0).sum()
        print(f"  {name}: nonzero in {nz}/{len(col)} rows ({100*nz/len(col):.1f}%), "
              f"mean={col.mean():.2f}, max={col.max():.1f}")
    print(f"  total_tokens: mean={y_tc.mean():.1f}, median={np.median(y_tc):.1f}, max={y_tc.max():.0f}")

    result = {
        "fit_full": {
            "n": len(rows),
            "r2": r2_full,
            "intercept": float(reg_full.intercept_),
            "coef_bash_ms": float(reg_full.coef_[0]),
            "coef_agent_count": float(reg_full.coef_[1]),
            "coef_edit_count": float(reg_full.coef_[2]),
            "residual_std": float(resid_full.std()),
        },
        "fit_tool_calls_only": {
            "n": len(rows_tc),
            "r2": r2_tc,
            "intercept": float(reg_tc.intercept_),
            "coef_bash_ms": float(reg_tc.coef_[0]),
            "coef_agent_count": float(reg_tc.coef_[1]),
            "coef_edit_count": float(reg_tc.coef_[2]),
            "residual_std": float(resid_tc.std()),
        },
        "shipped_weights": {
            "W_BASH": W_BASH_SHIPPED,
            "W_AGENT": W_AGENT_SHIPPED,
            "W_EDIT": W_EDIT_SHIPPED,
        },
    }
    out_path = HERE / "regression_fit_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
