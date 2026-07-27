import numpy as np
from scipy.stats import binomtest, bootstrap
import matplotlib.pyplot as plt


def test_binomial_wilson(
    k : int,   # Veces del exito observado
    n : int,   # Tamaño de muestra
    p : float, # Proporción
    nivel_confianza : float = .95,
    method : str = 'wilson'
    ) -> binomtest:
    resultado = binomtest(k, n, p)

    res = resultado.proportion_ci(confidence_level=nivel_confianza,method = method)

    low, high = res

    print(f'[{low} - {p} - {high}]')

    return resultado

def plot_wilson_interval(
    test_binomial : binomtest, ## error conceptual
    proporcion : float,
    nivel_confianza : float = .95,
    method : str = 'wilson',
    ):

    center = proporcion

    res = test_binomial.proportion_ci(
        confidence_level= nivel_confianza,
        method = method
    )

    y = 1 

    low, high = res

    plt.plot(low, y, 'r+', markersize = 20, label = 'Low point')
    plt.plot(center, y, 'ro', markersize = 15, label = 'Centro')
    plt.plot(high, y, 'g+', markersize = 20, label = 'High point')
    plt.plot([low, high], [1,1], 'b--', linewidth = 2, markersize = 12)
    plt.title(f'Intervalo bajo el calculo de  {method}')

    plt.legend(markerscale = 0.5)
    plt.show()

    return



def lift_ab(x, y, axis=0):
    return np.mean(y, axis=axis) - np.mean(x, axis=axis)

def calcular_intervalos_bootstrap(
    data_a: list,
    data_b: list,
    nivel_confianza : float = .95
)-> bootstrap:
    """
    Calcula el uplift de una prueba A - B ya culminado utilizando bootstrap
    Esto es caro computacionalmente.
    """
    datos = (data_a,data_b)

    res = bootstrap(
        datos,
        statistic=lift_ab,
        confidence_level = nivel_confianza,
        n_resamples= 10_000,
        method='percentile',
        random_state = 42)


    return res

def conversion_rate_mean(data, axis = -1):
    return np.mean(data, axis = axis)


def boostrap_function(
    datos : list,
    nivel_confianza: float = .95
    ) -> bootstrap:

    boot = bootstrap(
        data = (datos, ),
        statistic= conversion_rate_mean,
        confidence_level = nivel_confianza,
        n_resamples = 10_000,
        method = 'percentile',
        random_state = 42
    )

    return  boot