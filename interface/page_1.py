from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Agents Intelligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# El primer archivo corresponde al experimento de seis clusters documentado en
# 05_visualization.ipynb. Los demás permiten abrir resultados de iteraciones previas.
DATA_CANDIDATES = (
    PROJECT_ROOT
    / "Data"
    / "checkpoints"
    / "drain_logs-2026-07-27"
    / "Kmeans_ver2"
    / "dataframe_drain_logs.parquet",
    PROJECT_ROOT
    / "Data"
    / "checkpoints"
    / "vercel_historic"
    / "Kmeans"
    / "X_labels.parquet",
    PROJECT_ROOT
    / "Data"
    / "checkpoints"
    / "drain_logs"
    / "Kmeans_ver2"
    / "dataframe_drain_logs.parquet",
    PROJECT_ROOT
    / "Data"
    / "checkpoints"
    / "drain_logs"
    / "Kmeans"
    / "dataframe_drain_logs.parquet",
    PROJECT_ROOT / "models" / "kmeans" / "results" / "labeled_frame.csv",
)

COLUMN_ALIASES = {
    "cluster": ("labels", "kmeans_labels"),
    "requests": ("conteo_requests", "routes_visited", "total_requests"),
    "unique_routes": ("unique_routes", "rutas_recorridas", "routes_visited"),
    "activity_ms": ("activity_window_ms",),
    "median_gap_ms": (
        "median_time_between_requests_ms",
        "median_time_between_requests_filled",
    ),
    "user_agent": ("proxy.userAgent", "requestUserAgent"),
    "client_ip": ("proxy.clientIp",),
    "fingerprint": ("ja4Digest",),
    "time_window": ("time_window",),
    "is_one_shot": ("is_one_shot",),
}

RISK_COLORS = {
    "Baja": "#3BA273",
    "Media": "#D4A017",
    "Alta": "#D64545",
}


def _read_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


@st.cache_data(show_spinner="Cargando resultados del modelo…")
def load_local_data() -> tuple[pd.DataFrame | None, str, tuple[str, ...]]:
    """Carga el primer resultado disponible sin depender del directorio de ejecución."""

    configured_path = os.environ.get("AGENTS_DATA_PATH")
    candidates = list(DATA_CANDIDATES)
    if configured_path:
        candidates.insert(0, Path(configured_path).expanduser())

    errors: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            frame = _read_frame(path)
            return frame, str(path), tuple(errors)
        except Exception as exc:  # La UI debe seguir disponible si un checkpoint está dañado.
            errors.append(f"{path.name}: {type(exc).__name__}: {exc}")

    return None, "Resumen demo anonimizado", tuple(errors)


def _find_column(frame: pd.DataFrame, canonical_name: str) -> str | None:
    return next(
        (name for name in COLUMN_ALIASES[canonical_name] if name in frame.columns),
        None,
    )


def normalize_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normaliza los esquemas producidos por las distintas iteraciones del proyecto."""

    cluster_col = _find_column(frame, "cluster")
    requests_col = _find_column(frame, "requests")
    if cluster_col is None or requests_col is None:
        raise ValueError(
            "El archivo necesita una columna de cluster (labels/kmeans_labels) "
            "y una de volumen (conteo_requests/routes_visited/total_requests)."
        )

    normalized = pd.DataFrame(index=frame.index)
    normalized["cluster"] = pd.to_numeric(frame[cluster_col], errors="coerce")
    normalized["requests"] = pd.to_numeric(frame[requests_col], errors="coerce")

    numeric_defaults = {
        "unique_routes": "requests",
        "activity_ms": None,
        "median_gap_ms": None,
    }
    for target, default_from in numeric_defaults.items():
        source = _find_column(frame, target)
        if source:
            normalized[target] = pd.to_numeric(frame[source], errors="coerce")
        elif default_from:
            normalized[target] = normalized[default_from]
        else:
            normalized[target] = 0.0

    text_defaults = {
        "user_agent": "No disponible",
        "client_ip": "No disponible",
        "fingerprint": "No disponible",
    }
    for target, default in text_defaults.items():
        source = _find_column(frame, target)
        normalized[target] = (
            frame[source].fillna(default).astype(str) if source else default
        )

    one_shot_col = _find_column(frame, "is_one_shot")
    if one_shot_col:
        values = frame[one_shot_col]
        if pd.api.types.is_bool_dtype(values):
            normalized["is_one_shot"] = values.fillna(False)
        else:
            normalized["is_one_shot"] = (
                values.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})
            )
    else:
        normalized["is_one_shot"] = normalized["requests"].eq(1)

    time_col = _find_column(frame, "time_window")
    normalized["time_window"] = (
        pd.to_datetime(frame[time_col], errors="coerce", utc=True)
        if time_col
        else pd.NaT
    )

    normalized = normalized.dropna(subset=["cluster", "requests"])
    if normalized.empty:
        raise ValueError("El archivo no contiene observaciones válidas después de normalizarlo.")

    normalized["cluster"] = normalized["cluster"].astype(int)
    for column in ("requests", "unique_routes", "activity_ms", "median_gap_ms"):
        normalized[column] = normalized[column].fillna(0).clip(lower=0)

    return normalized


def summarize_data(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby("cluster", observed=True)
        .agg(
            groups=("cluster", "size"),
            requests_total=("requests", "sum"),
            unique_ips=("client_ip", "nunique"),
            unique_uas=("user_agent", "nunique"),
            avg_requests=("requests", "mean"),
            avg_activity_ms=("activity_ms", "mean"),
            avg_gap_ms=("median_gap_ms", "mean"),
            one_shot_share=("is_one_shot", "mean"),
        )
        .reset_index()
        .sort_values("cluster")
    )


def demo_summary() -> pd.DataFrame:
    """Resumen no sensible del experimento usado cuando Data/ no viaja con el repo."""

    return pd.DataFrame(
        [
            (0, 374, 793, 366, 68, 2.1203, 1720.6070, 1503.0695, 0.0000),
            (1, 3379, 3394, 1886, 243, 1.0044, 0.0065, 0.0064, 0.9967),
            (2, 58, 3100, 24, 5, 53.4483, 476358.8448, 6031.1638, 0.0000),
            (3, 390, 2132, 164, 38, 5.4667, 296415.1513, 55431.6987, 0.0000),
            (4, 106, 1475, 66, 12, 13.9151, 340490.1132, 15336.4198, 0.0000),
            (5, 693, 1613, 343, 52, 2.3276, 202128.8514, 163736.0108, 0.0000),
        ],
        columns=[
            "cluster",
            "groups",
            "requests_total",
            "unique_ips",
            "unique_uas",
            "avg_requests",
            "avg_activity_ms",
            "avg_gap_ms",
            "one_shot_share",
        ],
    )


def add_cluster_profiles(summary: pd.DataFrame) -> pd.DataFrame:
    """Asigna nombres descriptivos relativos; los IDs de K-Means no tienen semántica fija."""

    profiled = summary.copy()
    profiles = {int(cluster): "Navegación moderada" for cluster in profiled["cluster"]}

    one_shot_idx = profiled["one_shot_share"].idxmax()
    intense_idx = profiled["avg_requests"].idxmax()
    profiles[int(profiled.loc[one_shot_idx, "cluster"])] = "Sesiones de una solicitud"
    profiles[int(profiled.loc[intense_idx, "cluster"])] = "Navegación intensiva"

    remaining = profiled.loc[~profiled.index.isin({one_shot_idx, intense_idx})]
    if not remaining.empty:
        spaced_idx = remaining["avg_gap_ms"].idxmax()
        profiles[int(profiled.loc[spaced_idx, "cluster"])] = "Navegación espaciada"

        activity_candidates = remaining.drop(index=spaced_idx).sort_values("avg_requests")
        if len(activity_candidates) >= 2:
            light_idx = activity_candidates.index[0]
            elevated_idx = activity_candidates.index[-1]
            profiles[int(profiled.loc[light_idx, "cluster"])] = "Actividad mínima rápida"
            profiles[int(profiled.loc[elevated_idx, "cluster"])] = "Navegación elevada"

    request_rank = profiled["avg_requests"].rank(method="max", pct=True)
    profiled["profile"] = profiled["cluster"].map(profiles)
    profiled["risk"] = request_rank.map(
        lambda rank: "Alta" if rank >= 0.85 else ("Media" if rank >= 0.55 else "Baja")
    )
    profiled["display"] = profiled.apply(
        lambda row: f"Cluster {int(row['cluster'])} · {row['profile']}", axis=1
    )
    return profiled


def compact_duration(milliseconds: float) -> str:
    seconds = float(milliseconds) / 1000
    if seconds < 1:
        return f"{milliseconds:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    return f"{seconds / 60:.1f} min"


def masked_ip(value: str) -> str:
    parts = value.split(".")
    if len(parts) == 4:
        return ".".join(parts[:2] + ["×", "×"])
    if ":" in value:
        return f"{value.split(':', 1)[0]}:…"
    return "No disponible" if value == "No disponible" else "Oculta"


raw_data, source, load_errors = load_local_data()
data: pd.DataFrame | None = None

if raw_data is not None:
    try:
        data = normalize_data(raw_data)
        summary = summarize_data(data)
        is_demo = False
    except (ValueError, TypeError) as exc:
        load_errors = (*load_errors, f"Esquema: {exc}")
        summary = demo_summary()
        source = "Resumen demo anonimizado"
        is_demo = True
else:
    summary = demo_summary()
    is_demo = True

summary = add_cluster_profiles(summary)
profile_map = summary.set_index("cluster")["profile"].to_dict()
risk_map = summary.set_index("cluster")["risk"].to_dict()

st.title("Agents Intelligence")
st.caption(
    "Segmentación de comportamiento en Vercel Log Drains · K-Means · "
    "apoyo para revisión humana"
)

with st.sidebar:
    st.header("Fuente de datos")
    if is_demo:
        st.info(
            "Modo demostración: se usa un resumen agregado y anonimizado porque "
            "los datos productivos no forman parte del repositorio."
        )
    else:
        st.success("Checkpoint local cargado")
    st.caption(source)

    if data is not None and data["time_window"].notna().any():
        first_date = data["time_window"].min().strftime("%d %b %Y")
        last_date = data["time_window"].max().strftime("%d %b %Y")
        st.caption(f"Periodo: {first_date} — {last_date}")

    st.divider()
    st.caption(
        "Para cargar otro resultado, define `AGENTS_DATA_PATH` con la ruta a un "
        "CSV o Parquet compatible."
    )
    if load_errors:
        with st.expander("Detalles de carga"):
            for error in load_errors:
                st.code(error, language=None)

total_requests = int(summary["requests_total"].sum())
total_groups = int(summary["groups"].sum())
total_ips = int(summary["unique_ips"].sum()) if is_demo else int(data["client_ip"].nunique())
high_priority = int(summary.loc[summary["risk"].eq("Alta"), "groups"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Solicitudes analizadas", f"{total_requests:,}")
m2.metric("Ventanas de comportamiento", f"{total_groups:,}")
m3.metric("IPs únicas" if not is_demo else "Pares IP-cluster", f"{total_ips:,}")
m4.metric("Ventanas de prioridad alta", f"{high_priority:,}")

st.divider()

options = [None, *summary["cluster"].astype(int).tolist()]
selected_cluster = st.selectbox(
    "Explorar cluster",
    options,
    format_func=lambda value: (
        "Todos los clusters"
        if value is None
        else f"Cluster {value} · {profile_map.get(value, 'Sin perfil')}"
    ),
)

chart_col, detail_col = st.columns([1.7, 1])

with chart_col:
    st.subheader("Mapa de comportamiento")
    chart_data = summary.copy()
    chart_data["Prioridad"] = chart_data["risk"]
    chart_data["Solicitudes promedio"] = chart_data["avg_requests"]
    chart_data["Duración promedio (min)"] = chart_data["avg_activity_ms"] / 60000
    chart_data["Ventanas"] = chart_data["groups"]
    chart_data["Cluster"] = chart_data["cluster"].map(lambda value: f"C{int(value)}")
    chart_data["Color"] = chart_data["risk"].map(RISK_COLORS)

    st.scatter_chart(
        chart_data,
        x="Duración promedio (min)",
        y="Solicitudes promedio",
        size="Ventanas",
        color="Color",
        x_label="Duración promedio de actividad (min)",
        y_label="Solicitudes promedio por ventana",
        width="stretch",
    )
    st.caption(
        "Cada burbuja es un cluster; el tamaño representa cuántas ventanas contiene. "
        "La prioridad es relativa al volumen observado y no ejecuta acciones de firewall."
    )

with detail_col:
    st.subheader("Lectura del cluster")
    if selected_cluster is None:
        st.metric("Clusters identificados", len(summary))
        st.metric("Sesiones de una solicitud", f"{summary['one_shot_share'].mul(summary['groups']).sum():,.0f}")
        st.caption(
            "Selecciona un cluster para revisar su volumen, ritmo y diversidad de agentes."
        )
    else:
        row = summary.loc[summary["cluster"].eq(selected_cluster)].iloc[0]
        st.markdown(f"### {row['profile']}")
        st.caption(f"Prioridad de revisión: **{row['risk']}**")
        d1, d2 = st.columns(2)
        d1.metric("Solicitudes", f"{int(row['requests_total']):,}")
        d2.metric("Ventanas", f"{int(row['groups']):,}")
        d3, d4 = st.columns(2)
        d3.metric("IPs", f"{int(row['unique_ips']):,}")
        d4.metric("User agents", f"{int(row['unique_uas']):,}")
        st.progress(
            min(float(row["requests_total"] / total_requests), 1.0),
            text=f"Participación del tráfico · {row['requests_total'] / total_requests:.1%}",
        )
        st.caption(
            f"Ventana promedio: **{compact_duration(row['avg_activity_ms'])}** · "
            f"mediana entre solicitudes: **{compact_duration(row['avg_gap_ms'])}**"
        )

st.divider()
st.subheader("Resumen de clusters")

visible_summary = summary.copy()
visible_summary["Cluster"] = visible_summary["cluster"].map(lambda value: f"C{int(value)}")
visible_summary["Perfil"] = visible_summary["profile"]
visible_summary["Prioridad"] = visible_summary["risk"]
visible_summary["Ventanas"] = visible_summary["groups"].astype(int)
visible_summary["Solicitudes"] = visible_summary["requests_total"].astype(int)
visible_summary["Promedio por ventana"] = visible_summary["avg_requests"].round(2)
visible_summary["Actividad promedio"] = visible_summary["avg_activity_ms"].map(compact_duration)
visible_summary["Tiempo entre solicitudes"] = visible_summary["avg_gap_ms"].map(compact_duration)

st.dataframe(
    visible_summary[
        [
            "Cluster",
            "Perfil",
            "Prioridad",
            "Ventanas",
            "Solicitudes",
            "Promedio por ventana",
            "Actividad promedio",
            "Tiempo entre solicitudes",
        ]
    ],
    hide_index=True,
    width="stretch",
)

if data is not None:
    st.subheader("Muestra anonimizada")
    filtered = (
        data if selected_cluster is None else data[data["cluster"].eq(selected_cluster)]
    ).copy()
    filtered["Perfil"] = filtered["cluster"].map(profile_map)
    filtered["Cluster"] = filtered["cluster"].map(lambda value: f"C{int(value)}")
    filtered["Solicitudes"] = filtered["requests"].astype(int)
    filtered["Rutas únicas"] = filtered["unique_routes"].astype(int)
    filtered["Actividad"] = filtered["activity_ms"].map(compact_duration)
    filtered["IP anonimizada"] = filtered["client_ip"].map(masked_ip)
    filtered["User agent"] = filtered["user_agent"].str.slice(0, 110)

    st.dataframe(
        filtered[
            [
                "Cluster",
                "Perfil",
                "Solicitudes",
                "Rutas únicas",
                "Actividad",
                "IP anonimizada",
                "User agent",
            ]
        ].head(250),
        hide_index=True,
        width="stretch",
    )
    st.caption("Se muestran como máximo 250 registros y las direcciones IP están ocultas.")
else:
    st.caption(
        "La vista de registros se habilita automáticamente cuando existe un checkpoint local."
    )
