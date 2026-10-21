"""Official CFPB narrative archive, deterministic sampled benchmark, and provenance."""

import hashlib
import json
from pathlib import Path
import zipfile
import pandas as pd
import requests
from features import normalize, route

URL = "https://files.consumerfinance.gov/f/documents/CCDB_Export_1_December_2011_through_April_2018.zip"


def load_data(source=None):
    folder = Path(".data")
    folder.mkdir(exist_ok=True)
    archive = Path(source) if source else folder / "complaints.zip"
    if not archive.exists():
        # Stream the archive to avoid holding the compressed file in memory.
        with requests.get(URL, stream=True, timeout=120) as response:
            response.raise_for_status()
            with archive.open("wb") as f:
                for chunk in response.iter_content(1024 * 1024):
                    f.write(chunk)
    with archive.open("rb") as f:
        checksum = hashlib.file_digest(f, "sha256").hexdigest()
    rows = []
    scanned = 0
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(name) as f:
            for chunk in pd.read_csv(f, chunksize=20000, low_memory=False):
                scanned += len(chunk)
                chunk.columns = chunk.columns.str.strip()
                required = [
                    "Date received",
                    "Product",
                    "Consumer complaint narrative",
                    "Complaint ID",
                ]
                if not set(required) <= set(chunk):
                    raise ValueError("Archive schema changed")
                for date, product, text, identifier in chunk[required].itertuples(
                    index=False, name=None
                ):
                    if not isinstance(text, str) or len(text.strip()) < 40:
                        continue
                    label = route(str(product))
                    if label is None:
                        continue
                    # Stable 12.5% hash sample, independent of labels/outcomes.
                    if (
                        int(
                            hashlib.sha256(str(identifier).encode()).hexdigest()[:8], 16
                        )
                        % 8
                    ):
                        continue
                    clean = normalize(text)
                    rows.append(
                        dict(
                            id=str(identifier),
                            date=str(date),
                            text=clean,
                            label=label,
                            text_hash=hashlib.sha256(clean.encode()).hexdigest(),
                        )
                    )
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame.date, errors="raise")
    frame = frame.sort_values(["date", "id"]).drop_duplicates("text_hash", keep="first")
    frame = frame[frame.date >= "2015-01-01"].reset_index(drop=True)
    manifest = dict(
        source_url=URL,
        sha256=checksum,
        archive_rows=scanned,
        sample_rows=len(frame),
        sample_rule="SHA256(complaint ID) first 8 hex digits mod 8 equals zero; six mapped routes; >=40 text chars; >=2015; earliest exact-text duplicate retained",
        duplicate_control="Normalized exact hash; near-duplicate template overlap remains possible",
        availability="Live narratives removed September 2026; use official historical archive.",
        selection_bias="Public consented narratives and selected six product routes; not all complaints.",
    )
    Path("manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return frame
