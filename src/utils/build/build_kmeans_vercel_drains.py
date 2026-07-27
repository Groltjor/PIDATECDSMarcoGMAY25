from supabase import create_client, Client
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import joblib

PROJECT_ROOT = Path.cwd().parent.parent.parent
SRC = PROJECT_ROOT / 'src'
MODELS = PROJECT_ROOT / 'models'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.gather import (
    load_data_from_table
)

from utils.feature_eng import (
    process_features_log_drains,
    preprocess_drain_logs
)

from utils.checkpoints import (
    check_for_negatives,
    save_checkpoint
)

from utils.pipelines import (
    build_preprocess_base,
    build_kmeans_from_preprocessor
)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



folder_name = os.path.join(str(MODELS), 'kmeans')
os.makedirs(folder_name, exist_ok= True)
data_route = os.path.join(folder_name, 'data')
os.makedirs(data_route, exist_ok= True)
models_route = os.path.join(folder_name, 'models')
os.makedirs(models_route, exist_ok= True)

KMEANS_FOLDER = PROJECT_ROOT / folder_name

CHECKPOINT_MODEL = KMEANS_FOLDER / 'checkpoints'
CHECKPOINT_MODEL.mkdir(parents = True, exist_ok = True)

RESULTS_FOLDER = KMEANS_FOLDER / 'results'
RESULTS_FOLDER.mkdir(parents = True, exist_ok= True)


def ask_for_data(
    nombre_tabla : str = 'vercel_logs_buffer',
    desicion : bool = False
    ) -> pd.DataFrame:

    print(f'Desicion del usuario {desicion}')

    data_route = PROJECT_ROOT / 'models' / 'kmeans' / 'data'
    data_route.mkdir(parents = True, exist_ok = True)

    if desicion:

        print('Iniciando extracció de datos. Esto puede tardar varios minutos')
        data = load_data_from_table(nombre_tabla, supabase)
        run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        data_frame = pd.DataFrame(data)

        log_drains = pd.json_normalize(data_frame['log'])

        log_drains_clean = preprocess_drain_logs(log_drains)


        file_name = f'raw_train_data_{run_timestamp}.parquet'
        save_route_parquet = data_route / file_name
        log_drains_clean.to_parquet(save_route_parquet, index = False)

        print(f'Archivo almacenado en: {save_route_parquet}')
    
    else:

        
        
        parquet_files = list(data_route.glob('raw_train_data_*.parquet'))
        
        if len(parquet_files) == 0:
            raise FileNotFoundError(
                f'No se encontro ningún archivo en  {data_route}'
            )
        if len(parquet_files) > 1:
            raise ValueError('Mas de un archivo en la ruta')
        
        save_route_parquet = parquet_files[0]
        log_drains = pd.read_parquet(save_route_parquet)
        print(f'Archivo cargado desde: {save_route_parquet}')

    return log_drains

def ask_for_get_respuesta() -> bool:
    respuesta = input('Descargar fresh data desde Supabase? (Y/N)')

    return respuesta.strip().lower() in [
        'y', 'yes',
        's', 'si', 'sí',
        'true', 't'
    ]

def ask_for_nombre_tabla() -> str:
    nombre_tabla = input('Proporcionar nombre de tabla:')

    return nombre_tabla.strip().lower()

decision = ask_for_get_respuesta()

if decision:
    nombre_de_tabla_user = ask_for_nombre_tabla()
else:
    nombre_de_tabla_user = 'None'

log_drains = ask_for_data(nombre_de_tabla_user, decision)

X = process_features_log_drains(log_drains)
frame_drain = X.copy() ## cuidado con la memoria

numeric_cols = X.select_dtypes(include = 'number').columns
skew_values = X[numeric_cols].skew()

standard_cols = skew_values[skew_values.abs() < 1].index.tolist()
skewed_cols = skew_values[skew_values.abs() >= 1].index.tolist()

metadata = check_for_negatives(X[skewed_cols], standard_cols) 

print(metadata)

save_checkpoint(X, CHECKPOINT_MODEL, metadata)

drains_preprocessor = build_preprocess_base(metadata)

print(drains_preprocessor)

X  = frame_drain.drop(columns = ['ja4Digest','proxy.userAgent', 'proxy.clientIp']).copy()
cluster_size = 4
model = build_kmeans_from_preprocessor(drains_preprocessor, n = cluster_size) ## JAjaj deberia ser K
labels = model.fit_predict(X)

X_drains_labels = X.copy()
to_append = ['ja4Digest','proxy.userAgent', 'proxy.clientIp']

X_drains_labels[to_append] = frame_drain[to_append]
X_drains_labels['labels'] = labels

X_drains_labels.to_csv(os.path.join(RESULTS_FOLDER, 'labeled_frame.csv'))

run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

artifact = {
    "model": model,
    "metadata": metadata,
    "feature_cols": list(X.columns),
    "drop_cols": ['ja4Digest', 'proxy.userAgent', 'proxy.clientIp'],
    "id_cols": ['ja4Digest', 'proxy.userAgent', 'proxy.clientIp'],
    "n_clusters": cluster_size,
    "created_at": run_timestamp,
    "model_name": "kmeans_vercel_drains",
    "description": "Pipeline entrenado para clasificar comportamiento de agentes desde Vercel Log Drains"
}

model_file_name = f'kmeans_vercel_drains_{run_timestamp}.joblib'
model_path = os.path.join(models_route, model_file_name)

joblib.dump(artifact, model_path)

print(f'Modelo almacenado en: {model_path}')