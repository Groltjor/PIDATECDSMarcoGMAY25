from scipy.sparse import random
from sklearn.cluster import _bisect_k_means
import pandas as pd

import json

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import (
    OneHotEncoder, PowerTransformer, StandardScaler, 
    FunctionTransformer
)
from sklearn.pipeline import Pipeline

import numpy as np

def cast_to_int(x):
    return x.astype(int)

def build_preprocess_base(metadata : dict):

    cols_to_np1log = metadata['cols_to_np1log']
    cols_to_yeo = metadata['cols_to_yeo']
    cols_to_one_hot = metadata['cols_to_onehot']
    cols_to_standard = metadata['cols_to_standard'] ## Nota tenemos un bug, en 03
    cols_to_function = metadata['cols_to_function']

    log1p_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy = 'median')),
        ('np1log', FunctionTransformer(np.log1p, feature_names_out='one-to-one')),
        ('scaler', StandardScaler())
    ])

    function_map = Pipeline(steps = [
        ('imputer', SimpleImputer(strategy = 'median')),
        ('map', FunctionTransformer(cast_to_int, feature_names_out='one-to-one')),
    ])

    yeo_transformer = Pipeline(steps = [
        ('imputer', SimpleImputer(strategy = 'median')),
        ('yeo', PowerTransformer(method='yeo-johnson')),
        ('scaler', StandardScaler())
    ])

    onehot_transformer = Pipeline(steps = [
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore')),
    ])

    numeric_pipeline = Pipeline(steps = [
        ('imputer', SimpleImputer(strategy= 'median')),
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers = [
            ('log1p', log1p_transformer, cols_to_np1log),
            ('maper', function_map, cols_to_function),
            ('yeo', yeo_transformer, cols_to_yeo),
            ('cat', onehot_transformer, cols_to_one_hot),
            ('num', numeric_pipeline, cols_to_standard)
        ],
        remainder = 'drop'
    )

    return  preprocessor


def build_kmeans_from_preprocessor(
    preprocessor : ColumnTransformer,
    n : int = 2,
    rd_state : int = 42,
)-> Pipeline:

    model = KMeans(
        n_clusters= n,
        random_state = rd_state
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])

    return pipeline

def build_dbscan_preprocessor(
    preprocessor: ColumnTransformer,
    min_samples : int = 5,
    eps = 0.05,
) -> Pipeline:

    model = DBSCAN(
        eps=eps,
        min_samples=min_samples
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])

    return pipeline

def build_agglomerative_preprocessor(
    preprocessr: ColumnTransformer,
    n_clusters : int = 2,
    metric : str = 'euclidian'
) -> Pipeline:

    model = AgglomerativeClustering(
        n_clusters = n_clusters,
        metric = metric,
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessr),
        ('model', model)
    ])

    return pipeline