# Periodic Stability tools

Command-line utilities to compute chemistry-style **periodic descriptors** from public periodic-table JSON:

- **PSI (Periodic Stability Index):** \( \mathrm{IE}_1 / r \) with **IE\(_1\)** in eV and **\(r\)** in pm, so PSI is in **eV/pm** (a crude “energy per distance” scale).
- **Volumetric stability:** \( \mathrm{IE}_1 / V \) where \(V=\frac{4}{3}\pi r^3\) in **pm³**, reported as **eV/pm³**.
- **Mulliken / hardness style combinations** (gas-phase atom data, same units convention as many textbooks):
  - **Mulliken-like:** \((\mathrm{IE}_1 + \mathrm{EA})/2\) in eV (EA is treated as a signed energy in the dataset).
  - **Hardness-like:** \((\mathrm{IE}_1 - \mathrm{EA})/2\) in eV.

Data defaults to `pTable.json` from [sweaver2112/periodic-table-data-complete](https://github.com/sweaver2112/periodic-table-data-complete) (see that repository for licensing and provenance).

## Install

```bash
pip install -e .
```

## Build the table

```bash
periodic-stability build -o rows.json --csv rows.csv --cache .cache/pTable.json
```

Notes:

- **Radius choice:** covalent radius is preferred when present; otherwise empirical, calculated, then van der Waals (see `radius_source` in the output).
- **Units:** first ionization energies in the source file are treated as **kJ/mol** and converted to eV using ~96.485 kJ/mol per eV.

## Analyze the exported rows

```bash
periodic-stability analyze rows.json -o summary.json
```

The summary includes basic descriptive statistics for PSI, correlations vs Pauling (where both exist), and a few “top PSI” rows for quick sanity checks.

## Library use

```python
from periodic_stability.data import fetch_periodic_table_json
from periodic_stability.compute import build_rows
from periodic_stability.analyze import summarize

elements = fetch_periodic_table_json(cache_path=".cache/pTable.json")
rows = build_rows(elements)
print(summarize(rows)["correlations"])
```
