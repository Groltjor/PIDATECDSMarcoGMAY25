import supabase
import os
from supabase import create_client, Client
import pandas as pd
from pathlib import Path
import json
import supabase
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path.cwd().parent
SAVING_ROUTE_DATA = PROJECT_ROOT / 'Data' / 'csv'
PREPROCESSED = PROJECT_ROOT / 'Data' / 'processed'


def extract_and_save_data(
    supabase_client : Client,
    table_name : str,
    file_name : str,
    query: str = "*",
    batch_size : int = 20
    ) -> str:
    """
    1 hora documentada de code
    30 min de 
    Extrae data de supabase de las tablas corresponidientes
    """

    all_rows = []
    start = 0
    batch_size = 49

    print('Extrayendo data desde SUPABASE, este proceso tardará un par de minutos')

    while True:
        end = start + batch_size - 1

        response = (
            supabase_client
            .table(table_name)
            .select(query)
            .range(start, end)
            .execute()
        )

        rows = response.data
        
        if not rows:
            break
        all_rows.extend(rows)

        if len(rows) < batch_size:
            break
        start += batch_size

    print('Proceso terminado')
    data = pd.DataFrame(all_rows)

    print(f'Project Root {PROJECT_ROOT}')
    print(f'Almacenando en {SAVING_ROUTE_DATA}')

    os.makedirs(SAVING_ROUTE_DATA, exist_ok=True)

    file_to_save = os.path.join(SAVING_ROUTE_DATA, file_name)

    data.to_csv(file_to_save, index= False)

    return all_rows


def load_datasets(ruta_de_almacenado : Path = PREPROCESSED) -> tuple[list[pd.DataFrame], json]:
    """
    Documentadas 4 horas de proyecto en total Checkpoint
    """

    lista_datasets = []
    contenido = {}

    for ruta_archivo in sorted(ruta_de_almacenado.glob('*.csv')):

        data = pd.read_csv(str(ruta_archivo))
        lista_datasets.append(data)

        nombre_archivo = ruta_archivo.name
        
        data_json = {
            'nommbre_archivo' : nombre_archivo
        }

        contenido[str(ruta_archivo)] = data_json

    return lista_datasets, contenido


def load_data_from_table(
    nombre_tabla : str,
    supabase : Client,
    page_size : int = 999
    ):

    offset = 0
    all_data = []

    while True:

        response = (
            supabase
            .table(nombre_tabla)
            .select('*')
            .range(offset, offset + page_size - 1)
            .execute()
        )

        rows = response.data
        all_data.extend(rows)

        if not rows:
            break
            
        if len(rows) < page_size:
            break

        offset += page_size
    
    return all_data

def load_data_from_table_last_10(
    nombre_tabla : str,
    supabase : Client,
    page_size : int = 999
    ):

    offset = 0
    all_data = []

    now_utc = datetime.now(timezone.utc)
    ten_minutes_ago = now_utc - timedelta(minutes = 10)

    since = ten_minutes_ago.isoformat()

    while True:

        response = (
            supabase
            .table(nombre_tabla)
            .select('*')
            .gte('received_at', since)
            .order('received_at', desc = False)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        rows = response.data
        all_data.extend(rows)

        if not rows:
            break
            
        if len(rows) < page_size:
            break

        offset += page_size
    
    return all_data