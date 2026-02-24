"""
Cloud Function: Calculate Technical Indicators
Location: option2-gcp/cloud-functions/calculate_indicators/main.py

Triggered by: Pub/Sub topic "analyze-request"
Purpose: Fetch data from Finnhub (primary) / Alpha Vantage (fallback) and calculate technical indicators
"""

import base64
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from google.cloud import firestore, pubsub_v1, storage

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from technical_analysis_mcp.data import FinnhubAlphaDataFetcher, CachedDataFetcher
except ImportError:
    # Fallback if not in cloud run context
    FinnhubAlphaDataFetcher = None
    CachedDataFetcher = None

# Initialize clients
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
BUCKET_NAME = os.getenv("BUCKET_NAME", "technical-analysis-data")

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()


def calculate_indicators(event, context):
    """
    Main Cloud Function handler
    Triggered by Pub/Sub message
    """
    # Decode Pub/Sub message
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    
    symbol = data['symbol']
    period = data.get('period', '1mo')
    request_id = data.get('request_id')
    
    print(f"📊 Processing {symbol} (period: {period})")
    
    try:
        # Fetch data from Finnhub (primary) / Alpha Vantage (fallback)
        if FinnhubAlphaDataFetcher is None:
            raise ImportError("FinnhubAlphaDataFetcher not available")

        finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        av_key = os.getenv("ALPHA_VANTAGE_KEY", "")

        if not finnhub_key:
            raise ValueError("FINNHUB_API_KEY environment variable not set")

        # Create data fetcher with caching
        fetcher = FinnhubAlphaDataFetcher(
            finnhub_key=finnhub_key,
            alpha_vantage_key=av_key
        )
        cached_fetcher = CachedDataFetcher(fetcher)

        # Fetch data
        df = cached_fetcher.fetch(symbol, period)

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        print(f"✅ Fetched {len(df)} days of data")
        
        # Calculate indicators
        df = calculate_all_indicators(df)
        
        # Save to Cloud Storage
        save_to_storage(symbol, df)
        
        # Publish to next stage
        publish_next_stage(symbol, period, request_id, data)
        
        print(f"✅ Indicators calculated for {symbol}")
        
        return {"status": "success", "symbol": symbol}
    
    except Exception as e:
        print(f"❌ Error processing {symbol}: {e}")
        
        # Save error to Firestore
        db.collection("errors").document(f"{symbol}_{request_id}").set({
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now(),
            "stage": "calculate_indicators"
        })
        
        return {"status": "error", "symbol": symbol, "error": str(e)}


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators"""
    
    # Moving Averages
    for period in [5, 10, 20, 50, 100, 200]:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
    
    # Stochastic
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    # ADX
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    plus_dm = df['High'].diff()
    minus_dm = -df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr14 = true_range.rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr14)
    minus_di = 100 * (minus_dm.rolling(14).sum() / tr14)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    df['ADX'] = dx.rolling(14).mean()
    df['Plus_DI'] = plus_di
    df['Minus_DI'] = minus_di
    
    # ATR
    df['ATR'] = true_range.rolling(14).mean()
    
    # Volume indicators
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    df['Volume_MA_50'] = df['Volume'].rolling(window=50).mean()
    
    # OBV
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    
    # Price changes
    df['Price_Change'] = df['Close'].pct_change() * 100
    df['Price_Change_5d'] = ((df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5)) * 100
    
    # Volatility
    df['Volatility'] = df['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
    
    # Distance from MAs
    for period in [10, 20, 50, 200]:
        df[f'Dist_SMA_{period}'] = ((df['Close'] - df[f'SMA_{period}']) / df[f'SMA_{period}']) * 100
    
    return df


def save_to_storage(symbol: str, df: pd.DataFrame):
    """Save indicator data to Cloud Storage"""
    bucket = storage_client.bucket(BUCKET_NAME)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    blob_path = f"indicators/{date_str}/{symbol}-indicators.csv"
    
    blob = bucket.blob(blob_path)
    blob.upload_from_string(df.to_csv())
    
    print(f"💾 Saved to gs://{BUCKET_NAME}/{blob_path}")


def publish_next_stage(symbol: str, period: str, request_id: str, original_data: dict):
    """Publish to detect-signals topic"""
    topic_path = publisher.topic_path(PROJECT_ID, "indicators-complete")
    
    message_data = {
        "symbol": symbol,
        "period": period,
        "request_id": request_id,
        "include_ai": original_data.get("include_ai", True),
        "timestamp": datetime.now().isoformat()
    }
    
    future = publisher.publish(
        topic_path,
        data=json.dumps(message_data).encode("utf-8")
    )
    
    print(f"📤 Published to indicators-complete: {future.result()}")


if __name__ == "__main__":
    # Local testing
    test_event = {
        'data': base64.b64encode(json.dumps({
            "symbol": "AAPL",
            "period": "1mo",
            "request_id": "test123"
        }).encode('utf-8'))
    }
    
    result = calculate_indicators(test_event, None)
    print(f"Result: {result}")