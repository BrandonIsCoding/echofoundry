from quant.options import black_scholes_call


def main() -> None:
    spot = 100.0
    strike = 100.0
    rate = 0.05
    volatility = 0.20
    time_to_expiry = 1.0

    call_price = black_scholes_call(
        spot=spot,
        strike=strike,
        rate=rate,
        volatility=volatility,
        time_to_expiry=time_to_expiry,
    )

    print("Black-Scholes European Call Price")
    print("---------------------------------")
    print(f"Spot price:       {spot:.2f}")
    print(f"Strike price:     {strike:.2f}")
    print(f"Risk-free rate:   {rate:.2%}")
    print(f"Volatility:       {volatility:.2%}")
    print(f"Time to expiry:   {time_to_expiry:.2f} year(s)")
    print(f"Call price:       {call_price:.4f}")


if __name__ == "__main__":
    main()
