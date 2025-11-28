import pandas as pd

def featurize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['channel_UPI'] = (df['channel']=='UPI').astype(int)
    df['channel_QR'] = (df['channel']=='QR').astype(int)
    df['channel_LINK'] = (df['channel']=='LINK').astype(int)
    df['cat_UNKNOWN'] = (df['merchant_category']=='UNKNOWN').astype(int)
    df['hour_sin'] = (df['hour']/24*2*3.14159).apply(lambda x: __import__('math').sin(x))
    df['hour_cos'] = (df['hour']/24*2*3.14159).apply(lambda x: __import__('math').cos(x))
    cols = ['amount','day_of_week','user_tx_last_hour','merchant_tx_last_hour','channel_UPI','channel_QR','channel_LINK','cat_UNKNOWN','hour_sin','hour_cos']
    return df[cols]


if __name__ == "__main__":
    from dataset_generator import generate
    df = generate(10)
    X = featurize(df)
    print("Feature columns:", list(X.columns))
    print("\nSample features:\n")
    try:
        # pretty print without index
        print(X.head().to_string(index=False))
    except Exception:
        print(X.head())
