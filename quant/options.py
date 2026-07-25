from math import erf, exp, log, sqrt


def standard_normal_cdf(x: float) -> float:
    """Return the cumulative distribution function of the standard normal distribution."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def black_scholes_call(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    time_to_expiry: float,
) -> float:
    """
    Price a European call option using the Black-Scholes formula.

    Parameters
    ----------
    spot:
        Current price of the underlying asset. Usually written as S.
    strike:
        Option strike price. Usually written as K.
    rate:
        Continuously compounded risk-free interest rate. Usually written as r.
        Example: 0.05 means 5%.
    volatility:
        Annualized volatility of the underlying asset. Usually written as sigma.
        Example: 0.20 means 20%.
    time_to_expiry:
        Time to expiration in years. Usually written as T.
        Example: 0.5 means half a year.

    Returns
    -------
    float
        The theoretical Black-Scholes price of a European call option.

    Assumptions
    -----------
    This simplified version assumes:
    - European exercise only
    - no dividends
    - constant volatility
    - constant risk-free rate
    - frictionless markets
    """
    if spot <= 0:
        raise ValueError("spot must be positive.")
    if strike <= 0:
        raise ValueError("strike must be positive.")
    if volatility <= 0:
        raise ValueError("volatility must be positive.")
    if time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be positive.")

    d1 = (
        log(spot / strike)
        + (rate + 0.5 * volatility**2) * time_to_expiry
    ) / (volatility * sqrt(time_to_expiry))

    d2 = d1 - volatility * sqrt(time_to_expiry)

    call_price = (
        spot * standard_normal_cdf(d1)
        - strike * exp(-rate * time_to_expiry) * standard_normal_cdf(d2)
    )

    return call_price
