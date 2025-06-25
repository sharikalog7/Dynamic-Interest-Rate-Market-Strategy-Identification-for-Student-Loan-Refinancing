import numpy as np

def predict_interest_rate():
    """
    Dummy model: In production, use time series forecasting (Prophet, ARIMA, etc.)
    """
    base_rate = 5.0
    fluctuation = np.random.normal(0, 0.3)
    return max(2.5, base_rate + fluctuation)
