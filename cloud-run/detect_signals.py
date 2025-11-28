"""
Cloud Function: Detect Trading Signals
Location: option2-gcp/cloud-functions/detect_signals/main.py

Triggered by: Pub/Sub topic "indicators-complete"
Purpose: Detect 150+ trading signals from calculated indicators
"""

import base64
import json
import os
from datetime import datetime

import pandas as pd
from google.cloud import firestore, pubsub_v1, storage

# Initialize clients
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "technical-analysis-prod")
BUCKET_NAME = os.getenv("BUCKET_NAME", "technical-analysis-data")

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()


def detect_signals(event, context):
    """
    Main Cloud Function handler
    Triggered by Pub/Sub message from indicators-complete
    """
    # Decode message
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    
    symbol = data['symbol']
    request_id = data.get('request_id')
    
    print(f"🎯 Detecting signals for {symbol}")
    
    try:
        # Load indicator data from Cloud Storage
        df = load_indicator_data(symbol)
        
        # Detect signals
        signals = detect_all_signals(df)
        
        print(f"✅ Detected {len(signals)} signals for {symbol}")
        
        # Save to Firestore (temporary, before AI ranking)
        current = df.iloc[-1]
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now(),
            "price": float(current['Close']),
            "change": float(current.get('Price_Change', 0)),
            "signals": signals,
            "summary": {
                "total_signals": len(signals),
                "bullish": sum(1 for s in signals if 'BULLISH' in s['strength']),
                "bearish": sum(1 for s in signals if 'BEARISH' in s['strength']),
            },
            "indicators": {
                "rsi": float(current['RSI']),
                "macd": float(current['MACD']),
                "adx": float(current['ADX']),
                "volume": int(current['Volume'])
            },
            "ranked": False  # Not yet AI ranked
        }
        
        # Save to Firestore
        db.collection("signals").document(symbol).set(result)
        
        # If AI ranking requested, publish to next stage
        if data.get("include_ai", True):
            publish_for_ranking(symbol, request_id, signals, result)
        else:
            # Apply rule-based ranking
            rank_signals_local(signals)
            result['signals'] = signals
            result['ranked'] = True
            db.collection("signals").document(symbol).set(result)
        
        return {"status": "success", "symbol": symbol, "signals": len(signals)}
    
    except Exception as e:
        print(f"❌ Error detecting signals for {symbol}: {e}")
        
        db.collection("errors").document(f"{symbol}_{request_id}").set({
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now(),
            "stage": "detect_signals"
        })
        
        return {"status": "error", "symbol": symbol, "error": str(e)}


def load_indicator_data(symbol: str) -> pd.DataFrame:
    """Load indicator data from Cloud Storage"""
    bucket = storage_client.bucket(BUCKET_NAME)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    blob_path = f"indicators/{date_str}/{symbol}-indicators.csv"
    
    blob = bucket.blob(blob_path)
    csv_data = blob.download_as_text()
    
    df = pd.read_csv(pd.StringIO(csv_data), index_col=0, parse_dates=True)
    
    print(f"📥 Loaded {len(df)} rows from gs://{BUCKET_NAME}/{blob_path}")
    
    return df


def detect_all_signals(df: pd.DataFrame) -> list:
    """Detect all trading signals"""
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) > 2 else prev
    
    signals = []
    
    # Moving Average Crossovers
    if len(df) > 200 and prev['SMA_50'] <= prev['SMA_200'] and current['SMA_50'] > current['SMA_200']:
        signals.append({
            'signal': 'GOLDEN CROSS',
            'desc': '50 MA crossed above 200 MA',
            'strength': 'STRONG BULLISH',
            'category': 'MA_CROSS'
        })
    
    if len(df) > 200 and prev['SMA_50'] >= prev['SMA_200'] and current['SMA_50'] < current['SMA_200']:
        signals.append({
            'signal': 'DEATH CROSS',
            'desc': '50 MA crossed below 200 MA',
            'strength': 'STRONG BEARISH',
            'category': 'MA_CROSS'
        })
    
    if prev['Close'] <= prev['SMA_20'] and current['Close'] > current['SMA_20']:
        signals.append({
            'signal': 'PRICE ABOVE 20 MA',
            'desc': 'Price crossed above 20-day MA',
            'strength': 'BULLISH',
            'category': 'MA_CROSS'
        })
    
    # RSI Signals
    if current['RSI'] < 30:
        signals.append({
            'signal': 'RSI OVERSOLD',
            'desc': f"RSI at {current['RSI']:.1f}",
            'strength': 'BULLISH',
            'category': 'RSI'
        })
    
    if current['RSI'] > 70:
        signals.append({
            'signal': 'RSI OVERBOUGHT',
            'desc': f"RSI at {current['RSI']:.1f}",
            'strength': 'BEARISH',
            'category': 'RSI'
        })
    
    if current['RSI'] < 20:
        signals.append({
            'signal': 'RSI EXTREME OVERSOLD',
            'desc': f"RSI at {current['RSI']:.1f}",
            'strength': 'STRONG BULLISH',
            'category': 'RSI'
        })
    
    # MACD Signals
    if prev['MACD'] <= prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
        signals.append({
            'signal': 'MACD BULL CROSS',
            'desc': 'MACD crossed above signal',
            'strength': 'BULLISH',
            'category': 'MACD'
        })
    
    if prev['MACD'] >= prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
        signals.append({
            'signal': 'MACD BEAR CROSS',
            'desc': 'MACD crossed below signal',
            'strength': 'BEARISH',
            'category': 'MACD'
        })
    
    # Bollinger Bands
    if current['Close'] <= current['BB_Lower'] * 1.01:
        signals.append({
            'signal': 'AT LOWER BB',
            'desc': f"Price at ${current['BB_Lower']:.2f}",
            'strength': 'BULLISH',
            'category': 'BOLLINGER'
        })
    
    if current['Close'] >= current['BB_Upper'] * 0.99:
        signals.append({
            'signal': 'AT UPPER BB',
            'desc': f"Price at ${current['BB_Upper']:.2f}",
            'strength': 'BEARISH',
            'category': 'BOLLINGER'
        })
    
    # Volume Signals
    if current['Volume'] > current['Volume_MA_20'] * 2:
        signals.append({
            'signal': 'VOLUME SPIKE 2X',
            'desc': f"Vol: {current['Volume']:,.0f}",
            'strength': 'SIGNIFICANT',
            'category': 'VOLUME'
        })
    
    if current['Volume'] > current['Volume_MA_20'] * 3:
        signals.append({
            'signal': 'EXTREME VOLUME 3X',
            'desc': f"Vol: {current['Volume']:,.0f}",
            'strength': 'VERY SIGNIFICANT',
            'category': 'VOLUME'
        })
    
    # ADX Trend Strength
    if current['ADX'] > 25:
        trend = 'UP' if current['Close'] > current['SMA_50'] else 'DOWN'
        signals.append({
            'signal': f'STRONG {trend}TREND',
            'desc': f"ADX: {current['ADX']:.1f}",
            'strength': 'TRENDING',
            'category': 'TREND'
        })
    
    # MA Alignment
    mas_aligned_bull = (current['SMA_10'] > current['SMA_20'] > current['SMA_50'])
    if mas_aligned_bull:
        signals.append({
            'signal': 'MA ALIGNMENT BULLISH',
            'desc': '10 > 20 > 50 SMA',
            'strength': 'STRONG BULLISH',
            'category': 'MA_TREND'
        })
    
    mas_aligned_bear = (current['SMA_10'] < current['SMA_20'] < current['SMA_50'])
    if mas_aligned_bear:
        signals.append({
            'signal': 'MA ALIGNMENT BEARISH',
            'desc': '10 < 20 < 50 SMA',
            'strength': 'STRONG BEARISH',
            'category': 'MA_TREND'
        })
    
    # Stochastic
    if current['Stoch_K'] < 20:
        signals.append({
            'signal': 'STOCHASTIC OVERSOLD',
            'desc': f"K at {current['Stoch_K']:.1f}",
            'strength': 'BULLISH',
            'category': 'STOCHASTIC'
        })
    
    if current['Stoch_K'] > 80:
        signals.append({
            'signal': 'STOCHASTIC OVERBOUGHT',
            'desc': f"K at {current['Stoch_K']:.1f}",
            'strength': 'BEARISH',
            'category': 'STOCHASTIC'
        })
    
    # Price Action
    if current['Price_Change'] > 5:
        signals.append({
            'signal': 'LARGE GAIN',
            'desc': f"+{current['Price_Change']:.1f}% today",
            'strength': 'STRONG BULLISH',
            'category': 'PRICE_ACTION'
        })
    
    if current['Price_Change'] < -5:
        signals.append({
            'signal': 'LARGE LOSS',
            'desc': f"{current['Price_Change']:.1f}% today",
            'strength': 'STRONG BEARISH',
            'category': 'PRICE_ACTION'
        })
    
    # Add more signals here... (can expand to 150+)
    
    return signals


def rank_signals_local(signals: list):
    """Rule-based ranking (fallback if no AI)"""
    for signal in signals:
        score = 50
        
        strength = signal.get('strength', '')
        if 'EXTREME' in strength:
            score = 85
        elif 'STRONG' in strength:
            score = 75
        elif 'SIGNIFICANT' in strength or 'VERY' in strength:
            score = 65
        elif 'BULLISH' in strength or 'BEARISH' in strength:
            score = 55
        
        category = signal.get('category', '')
        if category in ['MA_CROSS', 'MACD', 'VOLUME']:
            score += 10
        
        signal['ai_score'] = min(score, 95)
        signal['ai_reasoning'] = 'Rule-based score'
    
    signals.sort(key=lambda x: x['ai_score'], reverse=True)
    
    for rank, signal in enumerate(signals, 1):
        signal['rank'] = rank


def publish_for_ranking(symbol: str, request_id: str, signals: list, result: dict):
    """Publish to AI ranking topic"""
    topic_path = publisher.topic_path(PROJECT_ID, "signals-detected")
    
    message_data = {
        "symbol": symbol,
        "request_id": request_id,
        "signals": signals,
        "market_data": {
            "price": result["price"],
            "change": result["change"],
            "rsi": result["indicators"]["rsi"],
            "macd": result["indicators"]["macd"],
            "adx": result["indicators"]["adx"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    future = publisher.publish(
        topic_path,
        data=json.dumps(message_data).encode("utf-8")
    )
    
    print(f"📤 Published to signals-detected for AI ranking: {future.result()}")


if __name__ == "__main__":
    # Local testing
    test_event = {
        'data': base64.b64encode(json.dumps({
            "symbol": "AAPL",
            "request_id": "test123",
            "include_ai": True
        }).encode('utf-8'))
    }
    
    result = detect_signals(test_event, None)
    print(f"Result: {result}")