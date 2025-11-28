import numpy as np
import pandas as pd

CATEGORIES = ['GENERAL','FOOD','TRAVEL','BILLS','UNKNOWN']
CHANNELS = ['UPI','QR','LINK']

def generate(n: int = 10000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    user_ids = rng.integers(1, 1000, size=n)
    merchant_ids = rng.integers(1, 200, size=n)
    amounts = rng.gamma(2.0, 500.0, size=n).clip(1, 100000)
    channel = rng.choice(CHANNELS, size=n, p=[0.7,0.2,0.1])
    category = rng.choice(CATEGORIES, size=n, p=[0.4,0.2,0.2,0.15,0.05])
    hour = rng.integers(0,24,size=n)
    dow = rng.integers(0,7,size=n)
    user_burst = rng.poisson(2, size=n)
    merchant_burst = rng.poisson(5, size=n)

    # Hidden fraud pattern
    fraud_prob = 0.02 + (amounts>50000)*0.3 + (channel=='QR')*(amounts>10000)*0.2 + (category=='UNKNOWN')*0.15 + (user_burst>20)*0.3
    fraud = rng.random(size=n) < np.clip(fraud_prob, 0, 0.95)

    df = pd.DataFrame({
        'user_id': user_ids,
        'merchant_id': merchant_ids,
        'amount': amounts,
        'channel': channel,
        'merchant_category': category,
        'hour': hour,
        'day_of_week': dow,
        'user_tx_last_hour': user_burst,
        'merchant_tx_last_hour': merchant_burst,
        'is_fraud': fraud.astype(int)
    })
    return df

if __name__ == '__main__':
    df = generate(1000)
    print(df.head())
