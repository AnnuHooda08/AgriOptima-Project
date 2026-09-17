"""Sample official SoilGrids rasters into depth-specific location CSVs."""

from pathlib import Path
import csv

import numpy as np
from PIL import Image


SOURCE = Path("data/raw/soilgrids_haryana_punjab_bbox")
DEST = Path("data/processed/soilgrids_haryana_punjab_bbox")
DEPTHS = ("0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm")
PROPS = ("phh2o", "soc", "nitrogen", "sand", "silt", "clay", "bdod", "cec", "cfvo")
SCALE = {"phh2o": 10, "soc": 10, "nitrogen": 100, "sand": 10, "silt": 10,
         "clay": 10, "bdod": 100, "cec": 10, "cfvo": 10}
NAMES = ("ph_h2o", "organic_carbon_g_kg", "total_nitrogen_g_kg", "sand_pct",
         "silt_pct", "clay_pct", "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct")
STRIDE = 4  # one location from each 4x4 group of original 250 m cells


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for depth in DEPTHS:
        layers = []
        geo = None
        for prop in PROPS:
            path = SOURCE / f"{prop}_{depth}_mean.tif"
            with Image.open(path) as image:
                current_geo = (image.size, tuple(image.tag_v2[33550]), tuple(image.tag_v2[33922]))
                if geo is None:
                    geo = current_geo
                elif geo != current_geo:
                    raise ValueError(f"Grid mismatch in {path}")
                layers.append(np.asarray(image)[::STRIDE, ::STRIDE])

        (width, height), pixel_size, tie = geo
        output = DEST / f"soilgrids_{depth}.csv"
        rows = 0
        with output.open("w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(("latitude", "longitude", "depth_top_cm", "depth_bottom_cm") + NAMES)
            top, bottom = map(int, depth.removesuffix("cm").split("-"))
            for y in range(layers[0].shape[0]):
                lat = round(tie[4] - (y * STRIDE + 0.5) * pixel_size[1], 6)
                for x in range(layers[0].shape[1]):
                    raw = [int(layer[y, x]) for layer in layers]
                    # The WCS returns zero-filled pixels where the prediction is absent.
                    # pH and bulk density cannot physically be zero, so reject those cells.
                    if raw[0] == 0 or raw[6] == 0 or any(value < 0 or value >= 32767 for value in raw):
                        continue
                    lon = round(tie[3] + (x * STRIDE + 0.5) * pixel_size[0], 6)
                    writer.writerow((lat, lon, top, bottom) + tuple(round(value / SCALE[prop], 2) for value, prop in zip(raw, PROPS)))
                    rows += 1
        print(f"{output}: {rows} rows", flush=True)


if __name__ == "__main__":
    main()
