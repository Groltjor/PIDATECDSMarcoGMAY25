import pandas as pd
import numpy as np
from pathlib import Path
import os

def build_agents_frame(
    pre_frame: pd.DataFrame,
    group_cols: list[str] | None = None,
    timestamp_col: str = "timestampInMs",
) -> pd.DataFrame:
    """
    Construye un dataframe agregado por agente/región a partir de logs.

    Genera:
    - tiempo entre requests por grupo
    - conteos de requests
    - rutas únicas
    - conteos por status code
    - conteos por método HTTP
    - agregaciones de duración
    - agregaciones de memoria
    """

    if group_cols is None:
        group_cols = ["requestUserAgent", "region"]

    frame = pre_frame.copy()

    frame = frame.sort_values(
        group_cols + [timestamp_col]
    )

    frame["ms_since_previous_request"] = (
        frame
        .groupby(group_cols)[timestamp_col]
        .diff()
    )

    frame["seconds_since_previous_request"] = (
        frame["ms_since_previous_request"] / 1000
    )

    agents_frame = (
        frame
        .groupby(group_cols)
        .agg(
            total_requests=("requestPath", "count"),
            rutas_recorridas=("requestPath", "nunique"),

            status_200=("responseStatusCode", lambda x: (x == 200).sum()),
            status_301=("responseStatusCode", lambda x: (x == 301).sum()),
            status_302=("responseStatusCode", lambda x: (x == 302).sum()),
            status_304=("responseStatusCode", lambda x: (x == 304).sum()),
            status_400=("responseStatusCode", lambda x: (x == 400).sum()),
            status_401=("responseStatusCode", lambda x: (x == 401).sum()),
            status_403=("responseStatusCode", lambda x: (x == 403).sum()),
            status_404=("responseStatusCode", lambda x: (x == 404).sum()),
            status_405=("responseStatusCode", lambda x: (x == 405).sum()),
            status_500=("responseStatusCode", lambda x: (x == 500).sum()),

            get_requests=("requestMethod", lambda x: (x == "GET").sum()),
            post_requests=("requestMethod", lambda x: (x == "POST").sum()),
            head_requests=("requestMethod", lambda x: (x == "HEAD").sum()),

            ms_mean_duration=("durationMs", "mean"),
            ms_max_duration=("durationMs", "max"),
            ms_min_duration=("durationMs", "min"),
            ms_total_duration=("durationMs", "sum"),

            mem_mean_used=("maxMemoryUsed", "mean"),
            mem_max_used=("maxMemoryUsed", "max"),
            mem_min_used=("maxMemoryUsed", "min"),
            mem_total_used=("maxMemoryUsed", "sum"),

            mean_time_between_requests=("seconds_since_previous_request", "mean"),
            median_time_between_requests=("seconds_since_previous_request", "median"),
            min_time_between_requests=("seconds_since_previous_request", "min"),
            max_time_between_requests=("seconds_since_previous_request", "max"),

        )
        .reset_index()
    )

    return agents_frame


def build_ms_filling_columns(
    data_frame: pd.DataFrame
) -> tuple[pd.DataFrame, list, list]:

    data_frame = data_frame.copy()

    data_frame["is_one_shot"] = (
        data_frame["total_requests"] == 1
    ).astype("str")

    data_frame["mean_time_between_requests_filled"] = (
        data_frame["mean_time_between_requests"].fillna(-1)
    )

    data_frame["median_time_between_requests_filled"] = (
        data_frame["median_time_between_requests"].fillna(-1)
    )

    data_frame["min_time_between_requests_filled"] = (
        data_frame["min_time_between_requests"].fillna(-1)
    )

    data_frame["max_time_between_requests_filled"] = (
        data_frame["max_time_between_requests"].fillna(-1)
    )

    # Derivados nuevos usando solo lo que ya existe después del groupby
    data_frame["time_range_between_requests_filled"] = (
        data_frame["max_time_between_requests_filled"]
        - data_frame["min_time_between_requests_filled"]
    )

    data_frame["time_mean_median_gap_filled"] = (
        data_frame["mean_time_between_requests_filled"]
        - data_frame["median_time_between_requests_filled"]
    )

    data_frame["requests_per_route"] = np.where(
        data_frame["rutas_recorridas"] > 0,
        data_frame["total_requests"] / data_frame["rutas_recorridas"],
        data_frame["total_requests"]
    )

    data_frame["routes_per_request"] = np.where(
        data_frame["total_requests"] > 0,
        data_frame["rutas_recorridas"] / data_frame["total_requests"],
        0
    )

    cols_to_drop = [
        "mean_time_between_requests",
        "median_time_between_requests",
        "min_time_between_requests",
        "max_time_between_requests",
    ]

    cols_to_yeo = [
        "mean_time_between_requests_filled",
        "median_time_between_requests_filled",
        "min_time_between_requests_filled",
        "max_time_between_requests_filled",
        "time_range_between_requests_filled",
        "time_mean_median_gap_filled",
        "requests_per_route",
        "routes_per_request",
    ]

    return data_frame, cols_to_drop, cols_to_yeo



def process_features_log_drains(fuente_datos : pd.DataFrame) -> pd.DataFrame:
    """
    Esta es la función principal que genera los features relacionados
    Cambios en esta función genera cambios en como KMeans.
    """


    new_view = (
        fuente_datos
        .groupby([
            'ja4Digest','proxy.userAgent', 'proxy.clientIp'
    ])
        .agg(
            conteo_requests = ( 'path', 'count'),
            #times_timestamp = ( 'proxy.timestamp', 'count'),
            #request_amount = ( 'requestId', 'count'),
            #routes_visited = ( 'proxy.path', 'count'),

            activity_window_ms = (
                'proxy.timestamp',
                lambda x: x.max() - x.min()
            ),

            mean_time_between_requests_ms = (
                'proxy.timestamp',
                lambda x: x.sort_values().diff().mean()
            ),

            median_time_between_requests_ms = (
                'proxy.timestamp',
                lambda x : x.sort_values().diff().median()
            )  
        )
        .reset_index()
    )


    new_view = new_view.fillna({
        'mean_time_between_requests_ms' : 0,
        'median_time_between_requests_ms' : 0,
        'activity_window_ms' : 0,
    })

    new_view['is_one_shot'] = (new_view['conteo_requests'] == 1)

    return new_view

def preprocess_drain_logs(dataframe):

    cols_to_drop = [
    'id','host', 'level', 'branch', 'source',
    'projectId', 'environment', 'projectName',
    'deploymentId', 'executionRegion', 'proxy.host',
    'proxy.region', 'proxy.scheme', 'proxy.cacheId',
    'proxy.pathType', 'proxy.vercelId', 'proxy.vercelCache',
    'proxy.lambdaRegion', 'type', 'instanceId', 'statusCode', 'invocationId','proxy.pathTypeVariant'
    ]

    agents_clean_data = dataframe.drop(columns = cols_to_drop).copy()
    agents_clean_data['proxy.userAgent'] = agents_clean_data['proxy.userAgent'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
    )

    return agents_clean_data

def process_features_log_drains_ver2(fuente_datos : pd.DataFrame) -> pd.DataFrame:
    """
    Para mejorar este process es vital remover agrupacion por proxy.clientIP
    Revisar documentacion de Ja4, tambien se removie el user agent dado la preferencia
    por el footprint.
    """

    print('Estamos utilizando la Ver 2 de preprocesamiento de FE')

    ##

    df = fuente_datos.copy()

    df['timestamp_dt'] = pd.to_datetime(
        df['proxy.timestamp'],
        unit = 'ms',
        utc = 'True',
        errors = 'Coerce'
    )

    df = df.dropna(subset = ['timestamp_dt', 'ja4Digest'])
    df['time_window'] = df['timestamp_dt'].dt.floor('10min')

    new_view = (
        df
        .groupby([
            'ja4Digest',
            'time_window',
            'proxy.userAgent',
            'proxy.clientIp'
    ],
    observed = True,)
        .agg(
            routes_visited = ( 'proxy.path', 'count'),
            unique_routes = ( 'proxy.path', 'nunique'),

            activity_window_ms = (
                'proxy.timestamp',
                lambda x: x.max() - x.min()
            ),

            mean_time_between_requests_ms = (
                'proxy.timestamp',
                lambda x: x.sort_values().diff().mean()
            ),

            median_time_between_requests_ms = (
                'proxy.timestamp',
                lambda x : x.sort_values().diff().median()
            )
            
        )
        .reset_index()
    )

    time_columns = [
        "activity_window_ms",
        "mean_time_between_requests_ms",
        "median_time_between_requests_ms",
    ]

    new_view[time_columns] = new_view[time_columns].fillna(0)
    new_view['is_one_shot'] = (new_view['routes_visited'] == 1)

    return new_view



