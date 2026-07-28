# PIDA — Certificación en Ciencia de Datos del Tecnológico de Monterrey

Este repositorio contiene la evidencia y el código desarrollado para el proyecto integrador de la certificación. El proyecto parte del análisis de métricas de negocio de **edunautica.mx** y evoluciona hacia la identificación de patrones de tráfico automatizado mediante técnicas de _machine learning_ no supervisado.

## Guía rápida para el evaluador

La entrega **no está contenida únicamente en los notebooks**:

- [`Notebooks/`](Notebooks/) presenta el proceso, las decisiones, los experimentos y los resultados.
- [`src/utils/`](src/utils/) contiene las funciones reutilizables de extracción, limpieza, análisis, ingeniería de características y entrenamiento.
- [Conclusiones](Conclusiones.MD) presenta las conclusiones recopiladas del proyecto y sobre el modelo seleccionado.
- [Interface - Streamlit](interface) contiene una interfaz básica para el proyecto bajo la rúbrica del Tec.

Así mismo dentro del siguiente enlace se encuentra la versión demo con interfaz y como se comportaria con el modelo cargado dentro de una interfaz de Next.JS, estos contenidos estan fuera del scope del proyecto de certificación original y podria considerarse como opcional, sin embargo es mi entregable que cumple con los objetivos de proyecto final.

- [Vercel - App](https://log-hound.vercel.app) Contiene una simulación sin datos de la version final de la app en next.js.
- [Loghound Repo](https://github.com/Groltjor/LogHound) Contiene el repositorio final y reproducible del Producto de Machine Learning.

La versión anterior no contempla acciones de Firewall ni datos reales de producción, sin embargo se comparte como parte de la entrega, ya que la rubrica contempla una interfaz.

### Ejecutar la interfaz local

La interfaz carga el checkpoint local más reciente disponible. Si la carpeta `Data/` no está presente, muestra automáticamente un resumen agregado y anonimizado para demostración.

```bash
python -m pip install -r requirements.txt
streamlit run interface/interface_main.py
```

También puede cargarse otro resultado CSV o Parquet mediante la variable de entorno `AGENTS_DATA_PATH`. El archivo debe contener una etiqueta de cluster (`labels` o `kmeans_labels`) y una medida de volumen (`conteo_requests`, `routes_visited` o `total_requests`).

Los notebooks conservan sus salidas para que puedan revisarse sin volver a ejecutar el proyecto. El orden recomendado de lectura es el siguiente:

| Orden | Archivo                                                                  | Contenido principal                                                                                                                                                         |
| ----: | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|     0 | [`00_Preeweek.ipynb`](Notebooks/00_Preeweek.ipynb)                       | Investigación previa, fuentes consultadas, contexto de la recolección de datos y fundamentos de JA4/TLS.                                                                    |
|     1 | [`01_ETL.ipynb`](Notebooks/01_ETL.ipynb)                                 | Entendimiento, extracción y limpieza inicial de las fuentes de datos.                                                                                                       |
|     2 | [`02_EDA.ipynb`](Notebooks/02_EDA.ipynb)                                 | Análisis exploratorio: comienza con métricas de negocio y documenta el hallazgo de tráfico automatizado que redefine el problema.                                           |
|     3 | [`03_feature_engineering.ipynb`](Notebooks/03_feature_engineering.ipynb) | Limpieza e ingeniería de características basadas en el comportamiento de los agentes. También documenta iteraciones descartadas y el riesgo de _data leakage_ identificado. |
|     4 | [`04_train_pipelines.ipynb`](Notebooks/04_train_pipelines.ipynb)         | Entrenamiento y comparación de los modelos K-Means, DBSCAN y Agglomerative Clustering.                                                                                      |
|     5 | [`05_visualization.ipynb`](Notebooks/05_visualization.ipynb)             | Visualización e interpretación de los grupos obtenidos; selección de K-Means como modelo principal.                                                                         |

Para una revisión breve, se recomienda leer primero las introducciones y conclusiones de los notebooks `02`, `03` y `05`. En conjunto explican el descubrimiento del problema, la construcción de las variables y la interpretación del resultado final.

## Organización del código

Las funciones se separaron de los notebooks para evitar duplicación y mantener una implementación reutilizable:

| Archivo                                                                          | Responsabilidad                                                   |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [`gather.py`](src/utils/gather.py)                                               | Extracción y carga de datos.                                      |
| [`cleaner.py`](src/utils/cleaner.py)                                             | Limpieza de datos geográficos.                                    |
| [`statistics.py`](src/utils/statistics.py)                                       | Pruebas e intervalos estadísticos utilizados durante el análisis. |
| [`feature_eng.py`](src/utils/feature_eng.py)                                     | Agregación de logs e ingeniería de características.               |
| [`checkpoints.py`](src/utils/checkpoints.py)                                     | Guardado y recuperación de datos intermedios y metadatos.         |
| [`pipelines.py`](src/utils/pipelines.py)                                         | Preprocesamiento y construcción de los modelos de clustering.     |
| [`analyze.py`](src/utils/analyze.py)                                             | Resumen e interpretación de los clusters.                         |
| [`build_kmeans_vercel_drains.py`](src/utils/build/build_kmeans_vercel_drains.py) | Flujo integrado para entrenar y guardar el modelo K-Means.        |

## Datos y reproducibilidad

Los datos provienen de servicios productivos de edunautica.mx, entre ellos Vercel Log Drains, Supabase y fuentes de analítica. El conjunto original contiene información sensible —como direcciones IP y registros de navegación—, por lo que **no se incluye en este repositorio**.

En consecuencia, la revisión principal debe realizarse sobre el código, la documentación y las salidas ya almacenadas en los notebooks. La ejecución completa requiere acceso autorizado a las fuentes de datos y la configuración de sus credenciales correspondientes.

## Referencias

Las fuentes técnicas y lecturas utilizadas para fundamentar el caso están reunidas al inicio de [`00_Preeweek.ipynb`](Notebooks/00_Preeweek.ipynb). Incluyen documentación sobre Vercel Firewall, JA4, _TLS fingerprinting_ y extensiones TLS.
