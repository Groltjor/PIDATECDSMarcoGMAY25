# Selección del modelo de clustering

## Objetivo del análisis

El propósito del análisis fue identificar perfiles de comportamiento dentro de los registros de navegación, de manera que los grupos resultantes pudieran ser revisados por una persona y utilizados para tomar decisiones.

No se buscó únicamente obtener la mejor separación matemática posible, sino generar una segmentación:

- interpretable;
- manejable;
- consistente;
- útil para revisión humana;
- orientada a la detección de comportamientos atípicos o potencialmente automatizados.

Para ello se evaluaron tres algoritmos de clustering no supervisado:

1. K-Means.
2. DBSCAN.
3. Agglomerative Clustering.

Las variables consideradas describen principalmente el volumen y el ritmo de navegación:

- `routes_visited`: cantidad total de rutas visitadas;
- `unique_routes`: cantidad de rutas distintas;
- `activity_window_ms`: duración total de la actividad;
- `mean_time_between_requests_ms`: tiempo promedio entre solicitudes;
- `median_time_between_requests_ms`: mediana del tiempo entre solicitudes;
- `is_one_shot`: indicador de sesiones con una única solicitud.

---

# Comparación de modelos

## DBSCAN

DBSCAN identificó numerosos patrones locales muy específicos. Por ejemplo, separó sesiones con dos solicitudes realizadas en pocos milisegundos, sesiones con varias solicitudes separadas por minutos y grupos con una cantidad elevada de rutas visitadas.

Sin embargo, el resultado produjo más de veinte microclusters, además de un grupo de ruido identificado con la etiqueta `-1`.

Aunque los grupos encontrados tienen coherencia interna, su nivel de fragmentación dificulta su utilización en un proceso de revisión humana. Una persona tendría que analizar demasiadas categorías, varias de ellas con diferencias mínimas.

Por esta razón, DBSCAN se considera útil como método complementario para identificar anomalías o comportamientos poco frecuentes, pero no como el modelo principal de segmentación.

---

## Agglomerative Clustering

Agglomerative Clustering generó cinco grupos generales:

| Cluster | Perfil general                    |
| ------: | --------------------------------- |
|       0 | Navegación moderada y pausada     |
|       1 | Pocas rutas con intervalos largos |
|       2 | Actividad alta o intensiva        |
|       3 | Sesiones de una sola solicitud    |
|       4 | Actividad mínima y rápida         |

El modelo jerárquico encontró una estructura similar a la observada con K-Means. En particular, distinguió claramente:

- sesiones de una sola solicitud;
- navegación mínima y rápida;
- sesiones con pocas solicitudes muy separadas;
- navegación moderada;
- actividad intensiva.

Este resultado funciona como evidencia de que los perfiles identificados no dependen exclusivamente de un solo algoritmo.

Sin embargo, Agglomerative Clustering agrupó dentro de una misma categoría algunos niveles de actividad que K-Means consiguió separar con mayor detalle. Por ejemplo, la actividad alta y la actividad intensiva quedaron parcialmente condensadas en un mismo grupo.

---

# Modelo seleccionado: K-Means

Se seleccionó K-Means como modelo final porque produjo seis grupos claramente diferenciados, interpretables y suficientemente manejables para revisión humana.

El modelo permite distinguir tanto el volumen de navegación como el ritmo temporal de las solicitudes.

## Resumen de los grupos

| Cluster | Rutas promedio | Ventana de actividad | Intervalo promedio | Perfil                        |
| ------: | -------------: | -------------------: | -----------------: | ----------------------------- |
|       0 |           2.12 |        1.72 segundos |      1.52 segundos | Actividad mínima rápida       |
|       1 |           1.00 |   Prácticamente cero | Prácticamente cero | Sesión de una sola solicitud  |
|       2 |          53.45 |         7.94 minutos |     10.51 segundos | Actividad intensiva           |
|       3 |           5.47 |         4.94 minutos |     72.16 segundos | Navegación moderada y pausada |
|       4 |          13.92 |         5.67 minutos |     29.13 segundos | Navegación alta               |
|       5 |           2.33 |         3.37 minutos |    163.97 segundos | Actividad mínima espaciada    |

---

# Interpretación de los clusters

## Cluster 0: actividad mínima rápida

Este grupo contiene sesiones con aproximadamente dos rutas visitadas en una ventana de actividad cercana a dos segundos.

Características principales:

- pocas solicitudes;
- rutas casi siempre diferentes;
- actividad concentrada en un periodo muy corto;
- ausencia de comportamiento `one-shot`.

Este perfil puede representar sesiones muy breves, abandonos rápidos, precargas, verificaciones automáticas sencillas o solicitudes realizadas por servicios automatizados de baja intensidad.

Su interpretación requiere revisar los user agents y otros atributos asociados.

---

## Cluster 1: sesión de una sola solicitud

Este cluster contiene sesiones con exactamente una ruta visitada y una ventana de actividad prácticamente nula.

Características principales:

- una sola solicitud;
- una sola ruta;
- sin intervalo entre solicitudes;
- `is_one_shot = 1`.

Es el grupo más claramente definido.

Puede incluir usuarios que abandonaron el sitio después de la primera carga, solicitudes aisladas, verificaciones automáticas, crawlers o servicios que consultan únicamente un recurso.

El comportamiento no debe considerarse automáticamente malicioso, pero puede analizarse por separado debido a su naturaleza particular.

---

## Cluster 2: actividad intensiva

Este grupo registra en promedio más de cincuenta rutas dentro de una ventana aproximada de ocho minutos.

Características principales:

- volumen muy alto de rutas;
- una nueva solicitud aproximadamente cada diez segundos;
- gran cantidad de rutas únicas;
- actividad sostenida.

Es uno de los grupos con mayor prioridad para revisión.

El comportamiento podría corresponder a:

- navegación humana intensiva;
- crawlers;
- scrapers;
- herramientas automatizadas;
- procesos de indexación;
- user agents que recorren sistemáticamente el sitio.

La clasificación final requiere revisar muestras de user agents, direcciones IP, secuencias de rutas y regularidad temporal.

---

## Cluster 3: navegación moderada y pausada

Este grupo contiene sesiones con aproximadamente cinco rutas visitadas durante una ventana cercana a cinco minutos.

Características principales:

- volumen moderado;
- pausas relativamente largas;
- intervalo promedio superior a un minuto;
- navegación distribuida en el tiempo.

Es uno de los perfiles más compatibles con navegación humana deliberada.

Las pausas entre solicitudes podrían representar lectura, evaluación del contenido o interacción pausada con distintas páginas.

Sin embargo, no puede asumirse que todas las observaciones sean humanas únicamente por pertenecer a este cluster.

---

## Cluster 4: navegación alta

Este grupo presenta aproximadamente catorce rutas visitadas dentro de una ventana cercana a seis minutos.

Características principales:

- volumen alto;
- solicitudes frecuentes;
- intervalos promedio cercanos a treinta segundos;
- actividad sostenida, pero menos extrema que en el cluster 2.

Este perfil podría representar usuarios activos que exploran varias páginas, así como procesos automatizados con una frecuencia moderada.

La separación entre los clusters 4 y 2 resulta útil porque permite diferenciar actividad alta de actividad intensiva.

Esto facilita asignar distintos niveles de prioridad durante la revisión.

---

## Cluster 5: actividad mínima espaciada

Este grupo contiene pocas rutas, pero con intervalos muy largos entre solicitudes.

Características principales:

- aproximadamente dos rutas;
- ventana de actividad superior a tres minutos;
- intervalo promedio cercano a 164 segundos;
- comportamiento opuesto al cluster 0.

Aunque los clusters 0 y 5 presentan un volumen similar, su comportamiento temporal es claramente diferente.

El cluster 0 representa pocas solicitudes concentradas en segundos, mientras que el cluster 5 representa pocas solicitudes distribuidas durante varios minutos.

Este perfil puede corresponder a navegación humana pausada, pestañas abiertas durante cierto tiempo, reactivaciones de sesión o procesos automáticos de baja frecuencia.

---

# Razones para seleccionar K-Means

K-Means fue seleccionado como modelo final por las siguientes razones:

## Interpretabilidad

Los seis clusters tienen perfiles claramente diferenciados y pueden describirse mediante conceptos comprensibles:

- una sola solicitud;
- actividad mínima rápida;
- actividad mínima espaciada;
- navegación moderada;
- navegación alta;
- actividad intensiva.

## Cantidad manejable de grupos

Seis grupos representan un nivel adecuado de granularidad.

El modelo evita tanto una segmentación excesivamente general como la fragmentación observada con DBSCAN.

## Utilidad operativa

Los clusters pueden utilizarse para priorizar revisiones.

Por ejemplo:

- el cluster 2 puede recibir prioridad alta por su volumen intensivo;
- el cluster 4 puede revisarse como actividad elevada;
- los clusters 0 y 1 pueden analizarse para identificar solicitudes automáticas o abandonos;
- los clusters 3 y 5 pueden compararse con patrones esperados de navegación humana.

## Diferenciación temporal

K-Means no agrupó las observaciones únicamente por cantidad de rutas.

También separó sesiones con volúmenes similares, pero ritmos diferentes.

El ejemplo más claro es la diferencia entre los clusters 0 y 5:

- ambos tienen aproximadamente dos rutas;
- el cluster 0 concentra la actividad en pocos segundos;
- el cluster 5 distribuye la actividad durante varios minutos.

Esta separación demuestra que el modelo incorpora tanto volumen como comportamiento temporal.

## Consistencia con Agglomerative Clustering

Agglomerative Clustering identificó perfiles generales semejantes.

La coincidencia entre ambos modelos respalda la existencia de una estructura consistente dentro de los datos.

K-Means conserva esta estructura, pero proporciona una separación más detallada entre navegación moderada, alta e intensiva.

---

# Uso propuesto del modelo

El modelo no determina por sí solo si una sesión pertenece a una persona o a un sistema automatizado.

Su función es reducir el espacio de análisis y organizar las observaciones en perfiles que puedan ser revisados.

El flujo de uso propuesto es:

1. Asignar cada registro a uno de los seis clusters.
2. Seleccionar muestras representativas de cada grupo.
3. Revisar user agents, direcciones IP y rutas visitadas.
4. Identificar comportamientos repetitivos o incompatibles con navegación humana.
5. Definir reglas, alertas o criterios de investigación.
6. Priorizar los clusters con mayor volumen o frecuencia de solicitudes.

De esta forma, el clustering funciona como una herramienta de apoyo para la toma de decisiones y no como una clasificación definitiva.

---

# Conclusión

Los tres algoritmos identificaron estructuras relevantes dentro de los registros.

DBSCAN encontró patrones locales y microclusters específicos, pero produjo una segmentación demasiado fragmentada para el objetivo de revisión humana.

Agglomerative Clustering identificó cinco perfiles generales y confirmó una estructura similar a la encontrada mediante K-Means, aunque agrupó algunos niveles de actividad dentro de categorías más amplias.

K-Means produjo seis grupos diferenciados, interpretables y operativamente manejables. Sus clusters representan distintos niveles de volumen y ritmo de navegación, desde sesiones de una sola solicitud hasta actividad intensiva de más de cincuenta rutas.

Por estas razones, K-Means fue seleccionado como modelo final para organizar los registros y facilitar la revisión humana de comportamientos potencialmente relevantes.
