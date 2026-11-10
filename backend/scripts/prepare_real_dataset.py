"""Prepare real e-commerce datasets for manual uploads (task 036).

Raw downloads live in ``backend/temp_data/<dataset>/`` (gitignored) and the
upload-ready CSV files are written to ``backend/temp_data/<dataset>/listos/``.

The script never cleans invalid rows: returns, zero prices and missing dates
must reach the upload so the ETL reports them. It only drops the columns that
identify a person, joins sheets, filters one store (Iowa) and splits each
dataset into non-overlapping periods that fit the upload limits.

Usage, from ``backend/``::

    python scripts/prepare_real_dataset.py online-retail-ii
    python scripts/prepare_real_dataset.py amazon-open-ecommerce
    python scripts/prepare_real_dataset.py iowa-stores --years 2012,2026
    python scripts/prepare_real_dataset.py iowa-liquor --store 2633 --years 2012-2026
"""

import argparse
import time
import urllib.request
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

DATA_ROOT = Path(__file__).resolve().parent.parent / "temp_data"

# Same limits as app.services.etl_service (MAX_ROWS default and MAX_UPLOAD_BYTES).
MAX_ROWS = 200_000
MAX_BYTES = 25 * 1024 * 1024

# Year -> dataset id on the Iowa Data Hub (from each year's catalog.data.gov page).
IOWA_DATASET_IDS = {year: 1249 + (year - 2012) for year in range(2012, 2027)}
IOWA_ROWS_URL = "https://idh-be.iowa.gov/api/v1/datasets/{id}/rows.csv"
IOWA_PAUSE_SECONDS = 10
USER_AGENT = "predicta-thesis-dataset-prep/1.0"

# Smaller periods tried in order until every file fits the limits.
PERIODS = ("Y", "6M", "Q", "M")


# ---------------------------------------------------------------- splitting


def _period_keys(dates: pd.Series, period: str) -> pd.Series:
    if period == "6M":
        return (
            dates.dt.year.astype(str)
            + "-S"
            + ((dates.dt.month - 1) // 6 + 1).astype(str)
        )
    return dates.dt.to_period(period).astype(str)


def _fits(frame: pd.DataFrame) -> bool:
    if len(frame) > MAX_ROWS:
        return False
    return len(frame.to_csv(index=False).encode("utf-8")) <= MAX_BYTES


def _split(
    frame: pd.DataFrame, dates: pd.Series, level: int = 0
) -> Iterator[tuple[str, pd.DataFrame]]:
    """Yield (label, rows) per period, using a smaller period only where needed."""
    if level >= len(PERIODS):
        raise SystemExit(
            "Un mes completo supera el límite de carga; hace falta dividir por día."
        )
    keys = _period_keys(dates, PERIODS[level])
    for key in sorted(keys.unique()):
        mask = keys == key
        chunk = frame[mask]
        if _fits(chunk):
            yield key, chunk
        else:
            yield from _split(chunk, dates[mask], level + 1)


def write_split(
    frame: pd.DataFrame, date_column: str, name: str, out_dir: Path
) -> None:
    """Write one CSV per period; rows whose date cannot be read go to their own file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.csv"):
        old.unlink()
    dates = pd.to_datetime(frame[date_column], errors="coerce")
    valid = dates.notna()
    written = 0
    print(f"{'archivo':45} {'filas':>9} {'MB':>7}  rango")
    for label, chunk in _split(frame[valid], dates[valid]):
        path = out_dir / f"{name}_{label}.csv"
        chunk.to_csv(path, index=False, encoding="utf-8")
        span = dates[chunk.index]
        written += len(chunk)
        size = path.stat().st_size / (1024 * 1024)
        print(
            f"{path.name:45} {len(chunk):>9,} {size:>7.1f}  {span.min():%Y-%m-%d} a {span.max():%Y-%m-%d}"
        )
    if not valid.all():
        path = out_dir / f"{name}_sin_fecha.csv"
        frame[~valid].to_csv(path, index=False, encoding="utf-8")
        written += int((~valid).sum())
        print(f"{path.name:45} {int((~valid).sum()):>9,}  filas sin fecha legible")
    print(f"Total escrito: {written:,} de {len(frame):,} filas.")
    if written != len(frame):
        raise SystemExit("La suma de filas no coincide con el origen.")


# ---------------------------------------------------------------- datasets


def _same_rows(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    """Compare two frames as multisets of rows, ignoring order."""
    if len(left) != len(right):
        return False
    columns = list(left.columns)
    as_text = [
        frame.astype(str).sort_values(columns).reset_index(drop=True)
        for frame in (left, right)
    ]
    return as_text[0].equals(as_text[1])


def prepare_online_retail_ii() -> None:
    folder = DATA_ROOT / "online-retail-ii"
    workbook = next(folder.glob("*.xlsx"), None)
    if workbook is None:
        with zipfile.ZipFile(folder / "online_retail_ii.zip") as archive:
            archive.extractall(folder)
        workbook = next(folder.glob("*.xlsx"))
    sheets = pd.read_excel(
        workbook, sheet_name=None, dtype={"Invoice": str, "StockCode": str}
    )
    for sheet, rows in sheets.items():
        print(
            f"Hoja {sheet!r}: {len(rows):,} filas, {rows['InvoiceDate'].min()} a {rows['InvoiceDate'].max()}"
        )
    # Each yearly sheet may repeat the last days of the previous one. Those rows are
    # the same transactions exported twice, so a later sheet keeps only what comes
    # after the previous sheet's last timestamp, once the repeated days are confirmed
    # identical.
    parts: list[pd.DataFrame] = []
    for rows in sheets.values():
        if parts:
            previous = parts[-1]
            cutoff = previous["InvoiceDate"].max()
            repeated = rows[rows["InvoiceDate"] <= cutoff]
            if len(repeated):
                same_days = previous[
                    previous["InvoiceDate"] >= repeated["InvoiceDate"].min()
                ]
                if not _same_rows(repeated, same_days):
                    raise SystemExit(
                        "Las hojas comparten días con filas distintas; revisar a mano."
                    )
                print(
                    f"Filas repetidas de la hoja anterior descartadas: {len(repeated):,}"
                )
            rows = rows[rows["InvoiceDate"] > cutoff]
        parts.append(rows)
    frame = pd.concat(parts, ignore_index=True).drop(columns=["Customer ID"])
    write_split(frame, "InvoiceDate", "online_retail_ii", folder / "listos")


def prepare_amazon() -> None:
    folder = DATA_ROOT / "amazon-open-ecommerce"
    frame = pd.read_csv(
        folder / "amazon-purchases.csv", dtype=str, keep_default_na=False
    )
    frame = frame.drop(columns=["Survey ResponseID"])
    write_split(frame, "Order Date", "amazon", folder / "listos")


def _download_iowa_year(year: int, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"iowa_{year}.zip"
    if target.exists():
        return target
    url = IOWA_ROWS_URL.format(id=IOWA_DATASET_IDS[year])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    print(f"Descargando {year} ...", flush=True)
    partial = target.with_suffix(".part")
    with (
        urllib.request.urlopen(request, timeout=600) as response,
        partial.open("wb") as out,
    ):
        while block := response.read(1024 * 1024):
            out.write(block)
    partial.rename(target)
    print(f"  {target.stat().st_size / (1024 * 1024):,.1f} MB", flush=True)
    time.sleep(IOWA_PAUSE_SECONDS)
    return target


def _iowa_chunks(archive_path: Path) -> Iterator[pd.DataFrame]:
    """Read every CSV part straight from the zip, without extracting it."""
    with zipfile.ZipFile(archive_path) as archive:
        for member in sorted(m for m in archive.namelist() if m.endswith(".csv")):
            with archive.open(member) as handle:
                yield from pd.read_csv(
                    handle, dtype=str, keep_default_na=False, chunksize=500_000
                )


def _parse_years(text: str) -> list[int]:
    if "-" in text:
        start, end = (int(part) for part in text.split("-"))
        return list(range(start, end + 1))
    return [int(part) for part in text.split(",")]


def iowa_stores(years: list[int]) -> None:
    """Rank the stores present in every given year by rows and months covered."""
    folder = DATA_ROOT / "iowa-liquor" / "descargas"
    summaries = []
    for year in years:
        counts: dict[tuple[str, str], int] = {}
        months: dict[str, set[str]] = {}
        for chunk in _iowa_chunks(_download_iowa_year(year, folder)):
            for key, size in chunk.groupby(["store_no", "store_name"]).size().items():
                counts[key] = counts.get(key, 0) + int(size)
            for store, month in zip(
                chunk["store_no"], chunk["ordered_on"].str[:7], strict=True
            ):
                months.setdefault(store, set()).add(month)
        summaries.append((year, counts, months))
    common = set.intersection(
        *({store for store, _ in counts} for _, counts, _ in summaries)
    )
    ranking = []
    for store in common:
        rows = [
            sum(n for (s, _), n in counts.items() if s == store)
            for _, counts, _ in summaries
        ]
        covered = [len(months.get(store, set())) for _, _, months in summaries]
        name = next(n for (s, n) in summaries[-1][1] if s == store)
        ranking.append((min(covered), sum(rows), store, name, rows, covered))
    ranking.sort(reverse=True)
    print("store_no | nombre | filas por año | meses con ventas por año")
    for _, _, store, name, rows, covered in ranking[:15]:
        print(f"{store} | {name} | {rows} | {covered}")


def prepare_iowa(store: str, years: list[int]) -> None:
    folder = DATA_ROOT / "iowa-liquor"
    out_dir = folder / "listos"
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for year in years:
        archive_path = _download_iowa_year(year, folder / "descargas")
        rows = pd.concat(
            [chunk[chunk["store_no"] == store] for chunk in _iowa_chunks(archive_path)],
            ignore_index=True,
        )
        name = f"iowa_{store}_{year}"
        for old in out_dir.glob(f"{name}*.csv"):
            old.unlink()
        dates = pd.to_datetime(rows["ordered_on"], errors="coerce")
        for label, chunk in _split(rows, dates):
            path = out_dir / f"iowa_{store}_{label}.csv"
            chunk.to_csv(path, index=False, encoding="utf-8")
            total += len(chunk)
            print(
                f"{path.name:35} {len(chunk):>8,} filas {path.stat().st_size / (1024 * 1024):>6.1f} MB"
            )
        if dates.isna().any():
            raise SystemExit(f"{year}: hay filas de la tienda sin fecha legible.")
        archive_path.unlink()
    print(f"Total de la tienda {store}: {total:,} filas.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "dataset",
        choices=[
            "online-retail-ii",
            "amazon-open-ecommerce",
            "iowa-stores",
            "iowa-liquor",
        ],
    )
    parser.add_argument("--store", help="store_no de Iowa")
    parser.add_argument("--years", default="2012-2026", help="2012-2026 o 2012,2026")
    args = parser.parse_args()

    if args.dataset == "online-retail-ii":
        prepare_online_retail_ii()
    elif args.dataset == "amazon-open-ecommerce":
        prepare_amazon()
    elif args.dataset == "iowa-stores":
        iowa_stores(_parse_years(args.years))
    else:
        if not args.store:
            parser.error("iowa-liquor necesita --store")
        prepare_iowa(args.store, _parse_years(args.years))


if __name__ == "__main__":
    main()
