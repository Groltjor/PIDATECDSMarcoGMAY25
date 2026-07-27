from unicodedata import numeric
import pandas as pd


def get_sizes_groups(
    data_frame : pd.DataFrame,
    kind : str,
    
    ) -> pd.DataFrame:

    sizes_cluster = (
        data_frame
        .groupby(kind)
        .size()
        .reset_index()
        .rename(columns = {0 : 'tamano'})
    )

    sizes_cluster['porcentajes'] = sizes_cluster['tamano'] / sizes_cluster['tamano'].sum()

    return sizes_cluster


def describe_clusters(
    data_frame : pd.DataFrame,
    kind : str,
    ) -> pd.DataFrame:

    cluster_describe = (
        data_frame
        .groupby(kind)
        .mean(numeric_only=True)
        .T
        .round(2)
    )

    return cluster_describe


def describe_clusters_median(
    data_frame : pd.DataFrame,
    kind = str,
    ) -> pd.DataFrame:

    cluster_describe = (
        data_frame
        .groupby(kind)
        .median(numeric_only=True)
        .T
    ).astype(int)

    return cluster_describe