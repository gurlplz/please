from __future__ import annotations

import json
from pathlib import Path
from statistics import correlation, mean, pstdev
from typing import Any, Iterable

from .compute import ElementRow


def _finite_pairs(
    rows: Iterable[ElementRow],
    x_attr: str,
    y_attr: str,
) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for r in rows:
        x = getattr(r, x_attr)
        y = getattr(r, y_attr)
        if x is None or y is None:
            continue
        xs.append(float(x))
        ys.append(float(y))
    return xs, ys


def pearson_r(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    try:
        return float(correlation(xs, ys))
    except Exception:
        return None


def summarize(rows: list[ElementRow]) -> dict[str, Any]:
    def stats(vals: list[float]) -> dict[str, float]:
        if not vals:
            return {}
        m = mean(vals)
        s = pstdev(vals) if len(vals) > 1 else 0.0
        return {"mean": m, "pstdev": s, "min": min(vals), "max": max(vals)}

    psi_vals = [r.psi_ev_per_pm for r in rows if r.psi_ev_per_pm is not None]
    pauling_vals = [r.pauling for r in rows if r.pauling is not None]

    px, py = _finite_pairs(rows, "psi_ev_per_pm", "pauling")
    mx, my = _finite_pairs(rows, "mulliken_ev", "pauling")
    hx, hy = _finite_pairs(rows, "hardness_ev", "pauling")

    missing_radius = sum(1 for r in rows if r.radius_pm is None)
    missing_ie = sum(1 for r in rows if r.ie1_ev is None)

    noble = {"He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"}
    noble_psi = [r.psi_ev_per_pm for r in rows if r.symbol in noble and r.psi_ev_per_pm is not None]

    by_period: dict[int, list[float]] = {}
    for r in rows:
        if r.period is None or r.psi_ev_per_pm is None:
            continue
        by_period.setdefault(r.period, []).append(r.psi_ev_per_pm)

    period_summary = {
        str(p): stats(v) for p, v in sorted(by_period.items(), key=lambda kv: kv[0])
    }

    return {
        "counts": {
            "elements": len(rows),
            "missing_first_ionization_energy": missing_ie,
            "missing_radius": missing_radius,
            "with_PSI": len(psi_vals),
            "with_Pauling": len(pauling_vals),
        },
        "PSI": stats([float(x) for x in psi_vals]),
        "Pauling": stats([float(x) for x in pauling_vals]),
        "correlations": {
            "pearson_PSI_vs_Pauling": pearson_r(px, py),
            "pearson_Mulliken_vs_Pauling": pearson_r(mx, my),
            "pearson_hardness_vs_Pauling": pearson_r(hx, hy),
        },
        "noble_gas_PSI": stats([float(x) for x in noble_psi]),
        "PSI_by_period": period_summary,
        "top_PSI": [
            r.to_json_dict()
            for r in sorted(
                (x for x in rows if x.psi_ev_per_pm is not None),
                key=lambda r: r.psi_ev_per_pm,
                reverse=True,
            )[:12]
        ],
    }


def load_rows_json(path: str | Path) -> list[ElementRow]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[ElementRow] = []
    for obj in raw:
        out.append(
            ElementRow(
                z=int(obj["Z"]),
                symbol=str(obj["symbol"]),
                name=str(obj.get("name") or ""),
                period=int(obj["period"]) if obj.get("period") is not None else None,
                group=int(obj["group"]) if obj.get("group") is not None else None,
                ie1_kj_mol=float(obj["IE1_kJ_mol"]) if obj.get("IE1_kJ_mol") is not None else None,
                ie1_ev=float(obj["IE1_eV"]) if obj.get("IE1_eV") is not None else None,
                electron_affinity_kj_mol=(
                    float(obj["EA_kJ_mol"]) if obj.get("EA_kJ_mol") is not None else None
                ),
                electron_affinity_ev=float(obj["EA_eV"]) if obj.get("EA_eV") is not None else None,
                radius_pm=float(obj["radius_pm"]) if obj.get("radius_pm") is not None else None,
                radius_source=str(obj["radius_source"]) if obj.get("radius_source") else None,
                pauling=(
                    float(obj["Pauling_electronegativity"])
                    if obj.get("Pauling_electronegativity") is not None
                    else None
                ),
                atomic_volume_pm3=(
                    float(obj["atomic_volume_pm3"])
                    if obj.get("atomic_volume_pm3") is not None
                    else None
                ),
                psi_ev_per_pm=(
                    float(obj["PSI_eV_per_pm"]) if obj.get("PSI_eV_per_pm") is not None else None
                ),
                energy_density_ev_per_pm3=(
                    float(obj["energy_density_eV_per_pm3"])
                    if obj.get("energy_density_eV_per_pm3") is not None
                    else None
                ),
                mulliken_ev=float(obj["Mulliken_eV"]) if obj.get("Mulliken_eV") is not None else None,
                hardness_ev=float(obj["hardness_eV"]) if obj.get("hardness_eV") is not None else None,
            )
        )
    return out


def write_csv(rows: list[ElementRow], path: str | Path) -> None:
    import csv

    path = Path(path)
    fieldnames = [
        "Z",
        "symbol",
        "name",
        "period",
        "group",
        "IE1_kJ_mol",
        "IE1_eV",
        "EA_kJ_mol",
        "EA_eV",
        "radius_pm",
        "radius_source",
        "Pauling_electronegativity",
        "atomic_volume_pm3",
        "PSI_eV_per_pm",
        "energy_density_eV_per_pm3",
        "Mulliken_eV",
        "hardness_eV",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r.to_json_dict())
