from __future__ import annotations

import numpy as np
from typing import Tuple

from plugins.tensorflow_classifier.tensor_utils.raster_source import RasterSource


class FeatureExtractor:
    @staticmethod
    def extract(
        raster: RasterSource,
        geopandas_frame,
        use_mask: bool = True,
        nodata_threshold: int = 250,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        if geopandas_frame is None or geopandas_frame.empty:
            raise ValueError("GeoDataFrame de amostras esta vazio")

        coords = [(float(x), float(y)) for x, y in zip(geopandas_frame.geometry.x, geopandas_frame.geometry.y)]
        valores = raster.sample(coords)

        if valores.ndim != 2:
            raise ValueError("A extracao espectral retornou um array com dimensoes invalidas")

        n_bands = raster.count
        has_alpha_band = use_mask and n_bands > 1
        if has_alpha_band:
            n_bands_feature = n_bands - 1
            x_all = valores[:, :n_bands_feature]
            valid_mask = valores[:, -1] >= nodata_threshold
        else:
            n_bands_feature = n_bands
            x_all = valores
            if use_mask:
                valid_mask = np.ones(x_all.shape[0], dtype=bool)
            else:
                valid_mask = ~np.all(x_all > nodata_threshold, axis=1)

        x_filtered = x_all[valid_mask]
        gdf_filtered = geopandas_frame.loc[valid_mask]

        if x_filtered.size == 0:
            raise ValueError("Nenhuma amostra valida apos aplicar mascara/nodata")

        if np.isnan(x_filtered).any():
            raise ValueError("Foram encontrados valores NaN na extracao espectral")

        y_filtered = gdf_filtered["id"].to_numpy(dtype=np.int32).reshape(-1, 1)
        return x_filtered.astype(np.float32), y_filtered, n_bands_feature
