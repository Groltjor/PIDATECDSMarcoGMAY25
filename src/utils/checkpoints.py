from numpy._core.defchararray import endswith
import pandas as pd
from pathlib import Path
import json
import os

def check_for_negatives(
    frame_candidatos : pd.DataFrame,
    standard_cols : list[str]
    
    ) -> dict:

    cols_to_yeo = []
    cols_to_np1log = []
    cols_to_onehot = []
    cols_to_standard = []
    colst_to_map_function = []

    for col in frame_candidatos.columns:
        serie = frame_candidatos[col]

        if col in standard_cols: ## Bug silencioso, nunca va entrear xD
            cols_to_standard.append(col)
            continue

        if pd.api.types.is_bool_dtype(serie):
            colst_to_map_function.append(col)
            continue

        if pd.api.types.is_numeric_dtype(serie):
            if (serie < 0).any():
                cols_to_yeo.append(col)
            else:
                cols_to_np1log.append(col)
        elif pd.api.types.is_string_dtype(serie) or serie.dtype == 'object':
            cols_to_onehot.append(col)
        
        metadata = {
            'cols_to_np1log' : cols_to_np1log,
            'cols_to_yeo' : cols_to_yeo,
            'cols_to_onehot' : cols_to_onehot,
            'cols_to_standard' : cols_to_standard,
            'cols_to_function' : colst_to_map_function
        }
    
    metadata['cols_to_standard'].extend(standard_cols)

    return metadata


def load_checkpoint(ruta_checkpoint : Path | str) -> dict[str]:

    ruta_checkpoint = Path(ruta_checkpoint)

    datos = {
        'dataframes' : [],
        'metadata': None,
    }

    for archivo in ruta_checkpoint.iterdir():

        if archivo.suffix == '.parquet':
            data = pd.read_parquet(archivo)
            datos['dataframes'].append(data)
        
        elif archivo.name == 'metadata.json':
            with open(archivo, 'r', encoding = 'utf-8') as jsonfile:
                datos['metadata'] = json.load(jsonfile)
    
    return datos

def save_checkpoint(
    data_frame : pd.DataFrame,
    ruta_checkpoint: Path,
    metadata : dict
):

    os.makedirs(str(ruta_checkpoint), exist_ok= True)

    meta_route = ruta_checkpoint / 'metadata.json'
    frame_path = ruta_checkpoint / 'data_frame.parquet'

    data_frame.to_parquet(str(frame_path))

    print(f'Almacenado parquet en: {str(frame_path)}')

    with open(str(meta_route), 'w', encoding = 'utf-8') as jsonfile:
        json.dump(metadata, jsonfile, indent=2)

    print(f'Almacenado metadata en: {str(meta_route)}')

    return