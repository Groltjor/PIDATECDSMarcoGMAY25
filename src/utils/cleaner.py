from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path.cwd().parent
SRC = PROJECT_ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def limpiar_geodatos(
    df : pd.DataFrame,
    col_lat : str ="latitud",
    col_lon : str ="longitud"
    ) -> pd.DataFrame:
    """
    Limpia un DataFrame con columnas de latitud y longitud:
    - Convierte a numérico (strings -> NaN si no se puede).
    - Elimina coordenadas fuera del rango aproximado de México.
    - Elimina coordenadas con valor (0,0).
    - Devuelve un DataFrame limpio con índices reiniciados.
    """

    # Copia para no modificar el original
    df = df.copy()

    # Asegurar valores numéricos
    df[col_lon] = pd.to_numeric(df[col_lon], errors="coerce")
    df[col_lat] = pd.to_numeric(df[col_lat], errors="coerce")

    # Rango aproximado para México
    mask_valid = (
        df[col_lon].between(-120, -85) &
        df[col_lat].between(14, 33) &
        ~((df[col_lon] == 0) & (df[col_lat] == 0))
    )

    # Filas inválidas
    invalid_idx = df.index[~mask_valid]
    print(f"Filas eliminadas: {len(invalid_idx)}")

    # Limpiar
    df = df[mask_valid].copy()
    df.reset_index(drop=True, inplace=True)

    return df
