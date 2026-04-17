from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

from .constants import KJ_PER_EV


def _first_ie_kj_mol(ionization_energies: Any) -> float | None:
    if not ionization_energies:
        return None
    if isinstance(ionization_energies, list) and ionization_energies:
        try:
            return float(ionization_energies[0])
        except (TypeError, ValueError):
            return None
    return None


def _radius_pm(radius_obj: Any) -> tuple[float | None, str | None]:
    if not isinstance(radius_obj, dict):
        return None, None
    order = ("covalent", "empirical", "calculated", "vanderwaals")
    for key in order:
        val = radius_obj.get(key)
        if val is None:
            continue
        try:
            r = float(val)
        except (TypeError, ValueError):
            continue
        if r > 0:
            return r, key
    return None, None


def _ea_kj_mol(ea: Any) -> float | None:
    if ea is None:
        return None
    try:
        return float(ea)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class ElementRow:
    z: int
    symbol: str
    name: str
    period: int | None
    group: int | None
    ie1_kj_mol: float | None
    ie1_ev: float | None
    electron_affinity_kj_mol: float | None
    electron_affinity_ev: float | None
    radius_pm: float | None
    radius_source: str | None
    pauling: float | None
    atomic_volume_pm3: float | None
    psi_ev_per_pm: float | None
    energy_density_ev_per_pm3: float | None
    mulliken_ev: float | None
    hardness_ev: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "Z": self.z,
            "symbol": self.symbol,
            "name": self.name,
            "period": self.period,
            "group": self.group,
            "IE1_kJ_mol": self.ie1_kj_mol,
            "IE1_eV": self.ie1_ev,
            "EA_kJ_mol": self.electron_affinity_kj_mol,
            "EA_eV": self.electron_affinity_ev,
            "radius_pm": self.radius_pm,
            "radius_source": self.radius_source,
            "Pauling_electronegativity": self.pauling,
            "atomic_volume_pm3": self.atomic_volume_pm3,
            "PSI_eV_per_pm": self.psi_ev_per_pm,
            "energy_density_eV_per_pm3": self.energy_density_ev_per_pm3,
            "Mulliken_eV": self.mulliken_ev,
            "hardness_eV": self.hardness_ev,
        }


def build_rows(elements: Iterable[dict[str, Any]]) -> list[ElementRow]:
    rows: list[ElementRow] = []
    for e in elements:
        z = int(e["atomic_number"])
        symbol = str(e["symbol"])
        name = str(e.get("name") or "")
        period = e.get("period")
        grp = e.get("group")
        period_i = int(period) if period is not None else None
        group_i = int(grp) if grp is not None else None

        ie1_kj = _first_ie_kj_mol(e.get("ionization_energies"))
        ie1_ev = ie1_kj / KJ_PER_EV if ie1_kj is not None else None

        ea_kj = _ea_kj_mol(e.get("electron_affinity"))
        ea_ev = ea_kj / KJ_PER_EV if ea_kj is not None else None

        r_pm, r_src = _radius_pm(e.get("radius"))

        pauling = e.get("electronegativity_pauling")
        try:
            pauling_f = float(pauling) if pauling is not None else None
        except (TypeError, ValueError):
            pauling_f = None

        vol = (4.0 / 3.0) * math.pi * (r_pm**3) if r_pm is not None else None

        psi = (ie1_ev / r_pm) if ie1_ev is not None and r_pm is not None and r_pm > 0 else None
        esd = (ie1_ev / vol) if ie1_ev is not None and vol is not None and vol > 0 else None

        mulliken = (
            (ie1_ev + ea_ev) / 2.0 if ie1_ev is not None and ea_ev is not None else None
        )
        hardness = (
            (ie1_ev - ea_ev) / 2.0 if ie1_ev is not None and ea_ev is not None else None
        )

        rows.append(
            ElementRow(
                z=z,
                symbol=symbol,
                name=name,
                period=period_i,
                group=group_i,
                ie1_kj_mol=ie1_kj,
                ie1_ev=ie1_ev,
                electron_affinity_kj_mol=ea_kj,
                electron_affinity_ev=ea_ev,
                radius_pm=r_pm,
                radius_source=r_src,
                pauling=pauling_f,
                atomic_volume_pm3=vol,
                psi_ev_per_pm=psi,
                energy_density_ev_per_pm3=esd,
                mulliken_ev=mulliken,
                hardness_ev=hardness,
            )
        )
    rows.sort(key=lambda r: r.z)
    return rows
