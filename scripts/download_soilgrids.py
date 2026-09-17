"""Download SoilGrids mean-prediction rasters for the Haryana/Punjab area."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import argparse
import shutil
import time


PROPERTIES = ("phh2o", "soc", "nitrogen", "sand", "silt", "clay", "bdod", "cec", "cfvo")
DEPTHS = ("0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm")
BBOX = (73.7, 27.5, 78.0, 32.7)  # lon min, lat min, lon max, lat max
BASE = "https://maps.isric.org/mapserv"


def fetch(task):
    prop, depth, root = task
    output = root / f"{prop}_{depth}_mean.tif"
    if output.exists() and output.stat().st_size > 1000:
        return output, "cached"
    params = [
        ("map", f"/map/{prop}.map"),
        ("SERVICE", "WCS"),
        ("VERSION", "2.0.1"),
        ("REQUEST", "GetCoverage"),
        ("COVERAGEID", f"{prop}_{depth}_mean"),
        ("FORMAT", "GEOTIFF_INT16"),
        ("SUBSET", f"Long({BBOX[0]},{BBOX[2]})"),
        ("SUBSET", f"Lat({BBOX[1]},{BBOX[3]})"),
        ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
        ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
    ]
    url = BASE + "?" + urlencode(params)
    temp = output.with_suffix(".part")
    for attempt in range(4):
        try:
            with urlopen(url, timeout=180) as response, temp.open("wb") as target:
                shutil.copyfileobj(response, target)
            with temp.open("rb") as source:
                if source.read(4) not in (b"II*\x00", b"MM\x00*"):
                    raise ValueError("Response was not a TIFF")
            temp.replace(output)
            return output, "downloaded"
        except Exception:
            temp.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/raw/soilgrids_haryana_punjab_bbox"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tasks = [(prop, depth, args.output) for prop in PROPERTIES for depth in DEPTHS]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                output, status = future.result()
                print(f"{status}: {output.name} ({output.stat().st_size} bytes)", flush=True)
            except Exception as error:
                print(f"FAILED: {task[0]} {task[1]}: {error}", flush=True)


if __name__ == "__main__":
    main()
