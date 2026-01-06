"""
Daily Stock Analysis Cloud Function

Automated technical analysis with Gemini AI ranking.
Triggered by Cloud Scheduler via Pub/Sub.

Uses the unified analysis library from src/technical_analysis_mcp/
to ensure single source of truth for all analysis logic.
"""

import functions_framework
from google.cloud import firestore
import os
import sys
from datetime import datetime
import time

# Add shared library to path
sys.path.insert(0, '/workspace')

from technical_analysis_mcp.analysis import StockAnalyzer
from technical_analysis_mcp.exceptions import (
    InvalidSymbolError,
    DataFetchError,
    InsufficientDataError,
)

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# Initialize clients
db = firestore.Client(project=PROJECT_ID) if PROJECT_ID else None

# Initialize analyzer with AI enabled if API key available
analyzer = StockAnalyzer(use_cache=True, use_ai=bool(GEMINI_API_KEY))

# Default watchlist
DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'MU', 'AMD', 'TSLA', 'META', 'SPY',
    'QQQ', 'IWM', 'XLF', 'XLK', 'DIA'
]


def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate technical indicators from price data."""
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # RSI (14-period)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_signal

    # Moving Averages
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    ema20 = close.ewm(span=20, adjust=False).mean()

    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + (2 * bb_std)
    bb_lower = bb_mid - (2 * bb_std)

    # ADX
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    # +DI and -DI
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    plus_di = 100 * (plus_dm.rolling(14).mean() / (atr + 1e-10))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (atr + 1e-10))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(14).mean()

    # Stochastic
    lowest_low = low.rolling(14).min()
    highest_high = high.rolling(14).max()
    stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
    stoch_d = stoch_k.rolling(3).mean()

    # Volume analysis
    vol_sma = volume.rolling(20).mean()
    vol_ratio = volume / (vol_sma + 1e-10)

    return {
        'price': float(close.iloc[-1]),
        'change_pct': float((close.iloc[-1] / close.iloc[-2] - 1) * 100),
        'rsi': float(rsi.iloc[-1]),
        'macd': float(macd.iloc[-1]),
        'macd_signal': float(macd_signal.iloc[-1]),
        'macd_hist': float(macd_hist.iloc[-1]),
        'sma20': float(sma20.iloc[-1]),
        'sma50': float(sma50.iloc[-1]),
        'ema20': float(ema20.iloc[-1]),
        'bb_upper': float(bb_upper.iloc[-1]),
        'bb_lower': float(bb_lower.iloc[-1]),
        'bb_mid': float(bb_mid.iloc[-1]),
        'adx': float(adx.iloc[-1]),
        'plus_di': float(plus_di.iloc[-1]),
        'minus_di': float(minus_di.iloc[-1]),
        'stoch_k': float(stoch_k.iloc[-1]),
        'stoch_d': float(stoch_d.iloc[-1]),
        'atr': float(atr.iloc[-1]),
        'volume': int(volume.iloc[-1]),
        'vol_avg': int(vol_sma.iloc[-1]),
        'vol_ratio': float(vol_ratio.iloc[-1])
    }


def detect_signals(ind: dict) -> list:
    """Detect trading signals from indicators."""
    signals = []

    # RSI signals
    if ind['rsi'] < 30:
        signals.append({
            'signal': 'RSI Oversold',
            'strength': 'STRONG BULLISH',
            'category': 'RSI',
            'value': round(ind['rsi'], 1)
        })
    elif ind['rsi'] < 40:
        signals.append({
            'signal': 'RSI Approaching Oversold',
            'strength': 'BULLISH',
            'category': 'RSI',
            'value': round(ind['rsi'], 1)
        })
    elif ind['rsi'] > 70:
        signals.append({
            'signal': 'RSI Overbought',
            'strength': 'STRONG BEARISH',
            'category': 'RSI',
            'value': round(ind['rsi'], 1)
        })
    elif ind['rsi'] > 60:
        signals.append({
            'signal': 'RSI Approaching Overbought',
            'strength': 'BEARISH',
            'category': 'RSI',
            'value': round(ind['rsi'], 1)
        })

    # MACD signals
    if ind['macd'] > ind['macd_signal'] and ind['macd_hist'] > 0:
        signals.append({
            'signal': 'MACD Bullish',
            'strength': 'BULLISH',
            'category': 'MACD',
            'value': round(ind['macd'], 4)
        })
    elif ind['macd'] < ind['macd_signal'] and ind['macd_hist'] < 0:
        signals.append({
            'signal': 'MACD Bearish',
            'strength': 'BEARISH',
            'category': 'MACD',
            'value': round(ind['macd'], 4)
        })

    # Moving average trend
    if ind['price'] > ind['sma20'] > ind['sma50']:
        signals.append({
            'signal': 'Uptrend (Price > SMA20 > SMA50)',
            'strength': 'BULLISH',
            'category': 'TREND'
        })
    elif ind['price'] < ind['sma20'] < ind['sma50']:
        signals.append({
            'signal': 'Downtrend (Price < SMA20 < SMA50)',
            'strength': 'BEARISH',
            'category': 'TREND'
        })

    # Golden/Death Cross proximity
    sma_diff_pct = (ind['sma20'] - ind['sma50']) / ind['sma50'] * 100
    if 0 < sma_diff_pct < 2:
        signals.append({
            'signal': 'Golden Cross Forming',
            'strength': 'BULLISH',
            'category': 'MA_CROSS'
        })
    elif -2 < sma_diff_pct < 0:
        signals.append({
            'signal': 'Death Cross Forming',
            'strength': 'BEARISH',
            'category': 'MA_CROSS'
        })

    # Bollinger Band signals
    if ind['price'] < ind['bb_lower']:
        signals.append({
            'signal': 'Price Below Lower Bollinger Band',
            'strength': 'STRONG BULLISH',
            'category': 'BOLLINGER'
        })
    elif ind['price'] > ind['bb_upper']:
        signals.append({
            'signal': 'Price Above Upper Bollinger Band',
            'strength': 'STRONG BEARISH',
            'category': 'BOLLINGER'
        })

    # ADX trend strength
    if ind['adx'] > 25:
        trend_dir = 'Bullish' if ind['plus_di'] > ind['minus_di'] else 'Bearish'
        signals.append({
            'signal': f'Strong {trend_dir} Trend (ADX > 25)',
            'strength': 'BULLISH' if trend_dir == 'Bullish' else 'BEARISH',
            'category': 'ADX',
            'value': round(ind['adx'], 1)
        })

    # Stochastic signals
    if ind['stoch_k'] < 20 and ind['stoch_d'] < 20:
        signals.append({
            'signal': 'Stochastic Oversold',
            'strength': 'BULLISH',
            'category': 'STOCHASTIC',
            'value': round(ind['stoch_k'], 1)
        })
    elif ind['stoch_k'] > 80 and ind['stoch_d'] > 80:
        signals.append({
            'signal': 'Stochastic Overbought',
            'strength': 'BEARISH',
            'category': 'STOCHASTIC',
            'value': round(ind['stoch_k'], 1)
        })

    # Volume signals
    if ind['vol_ratio'] > 2.0:
        signals.append({
            'signal': 'Volume Spike (2x+ average)',
            'strength': 'SIGNIFICANT',
            'category': 'VOLUME',
            'value': round(ind['vol_ratio'], 1)
        })
    elif ind['vol_ratio'] > 1.5:
        signals.append({
            'signal': 'Above Average Volume',
            'strength': 'NOTABLE',
            'category': 'VOLUME',
            'value': round(ind['vol_ratio'], 1)
        })

    return signals


def rank_with_gemini(symbol: str, indicators: dict, signals: list) -> dict:
    """Use Gemini AI to analyze and rank signals with exponential backoff."""
    if not model:
        return rule_based_score(signals)

    prompt = f"""Analyze {symbol} technical signals. Be concise.

PRICE: ${indicators['price']:.2f} ({indicators['change_pct']:+.2f}%)
RSI: {indicators['rsi']:.1f} | MACD: {indicators['macd']:.4f} | ADX: {indicators['adx']:.1f}

SIGNALS DETECTED:
{json.dumps([{'signal': s['signal'], 'strength': s['strength']} for s in signals], indent=2)}

Return ONLY valid JSON (no markdown):
{{"score": 1-100, "outlook": "BULLISH/BEARISH/NEUTRAL", "action": "BUY/SELL/HOLD", "confidence": "HIGH/MEDIUM/LOW", "summary": "1 sentence max"}}"""

    # Exponential backoff retry logic
    max_retries = 3
    base_delay = 2  # Start with 2 seconds

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Extract JSON
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()

            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                result = json.loads(text[start:end])
                result['ai_powered'] = True
                return result
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            if '429' in error_str or 'quota' in error_str.lower():
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4, 8 seconds
                    print(f"Rate limit for {symbol}, retrying after {delay}s...")
                    time.sleep(delay)
                    continue
            print(f"Gemini error for {symbol}: {e}")
            break

    return rule_based_score(signals)


def rule_based_score(signals: list) -> dict:
    """Fallback rule-based scoring."""
    bullish = sum(1 for s in signals if 'BULLISH' in s.get('strength', ''))
    bearish = sum(1 for s in signals if 'BEARISH' in s.get('strength', ''))

    score = 50 + (bullish - bearish) * 10
    score = max(10, min(90, score))

    if bullish > bearish + 2:
        outlook = 'BULLISH'
        action = 'BUY'
    elif bearish > bullish + 2:
        outlook = 'BEARISH'
        action = 'SELL'
    else:
        outlook = 'NEUTRAL'
        action = 'HOLD'

    return {
        'score': score,
        'outlook': outlook,
        'action': action,
        'confidence': 'MEDIUM',
        'summary': f'{bullish} bullish, {bearish} bearish signals',
        'ai_powered': False
    }


def analyze_symbol(symbol: str) -> dict:
    """Complete analysis for a single symbol using the unified analyzer.

    This function is now a thin wrapper around the StockAnalyzer from
    the technical_analysis_mcp library, ensuring single source of truth.
    """
    try:
        result = analyzer.analyze(symbol, period='3mo')
        return result
    except (InvalidSymbolError, DataFetchError, InsufficientDataError) as e:
        return {
            'symbol': symbol,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Unexpected error analyzing {symbol}: {e}")
        return {
            'symbol': symbol,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def save_to_firestore(results: list, summary: dict):
    """Save results to Firestore."""
    if not db:
        print("Firestore not configured, skipping save")
        return

    batch = db.batch()

    # Save individual analyses
    for result in results:
        if 'error' not in result:
            ref = db.collection('analysis').document(result['symbol'])
            batch.set(ref, result)

    # Save daily summary
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    summary_ref = db.collection('summaries').document(date_str)
    batch.set(summary_ref, summary)

    batch.commit()
    print(f"Saved {len(results)} analyses to Firestore")


@functions_framework.http
def daily_analysis_http(request):
    """HTTP-triggered analysis (for manual testing)."""
    return run_analysis()


@functions_framework.cloud_event
def daily_analysis_pubsub(cloud_event):
    """Pub/Sub triggered analysis (for scheduled runs)."""
    return run_analysis()


def run_analysis():
    """Main analysis logic."""
    print("=" * 60)
    print("DAILY STOCK ANALYSIS")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    watchlist = DEFAULT_WATCHLIST
    results = []

    for i, symbol in enumerate(watchlist):
        print(f"\n[{i+1}/{len(watchlist)}] Analyzing {symbol}...")
        result = analyze_symbol(symbol)
        results.append(result)

        if 'error' in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Price: ${result['price']:.2f} ({result['change_pct']:+.2f}%)")
            print(f"  Score: {result['ai_score']} | Outlook: {result['ai_outlook']}")
            print(f"  Signals: {result['signal_count']}")

        # Rate limiting: 6.5s delay stays under Gemini API limit (10 requests/min)
        if i < len(watchlist) - 1:
            time.sleep(6.5)

    # Create summary
    successful = [r for r in results if 'error' not in r]

    summary = {
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'timestamp': datetime.utcnow().isoformat(),
        'total_analyzed': len(results),
        'successful': len(successful),
        'errors': len(results) - len(successful),
        'top_bullish': sorted(
            [r for r in successful if r.get('ai_outlook') == 'BULLISH'],
            key=lambda x: x.get('ai_score', 0),
            reverse=True
        )[:5],
        'top_bearish': sorted(
            [r for r in successful if r.get('ai_outlook') == 'BEARISH'],
            key=lambda x: x.get('ai_score', 0),
            reverse=True
        )[:5],
        'high_confidence': [r for r in successful if r.get('ai_confidence') == 'HIGH']
    }

    # Save to Firestore
    save_to_firestore(results, summary)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Analyzed: {summary['successful']}/{summary['total_analyzed']}")

    if summary['top_bullish']:
        print("\nTop Bullish:")
        for r in summary['top_bullish'][:3]:
            print(f"  {r['symbol']}: Score {r['ai_score']} - {r.get('ai_summary', '')[:50]}")

    if summary['top_bearish']:
        print("\nTop Bearish:")
        for r in summary['top_bearish'][:3]:
            print(f"  {r['symbol']}: Score {r['ai_score']} - {r.get('ai_summary', '')[:50]}")

    return json.dumps({
        'status': 'success',
        'analyzed': summary['successful'],
        'errors': summary['errors'],
        'top_bullish': [r['symbol'] for r in summary['top_bullish']],
        'top_bearish': [r['symbol'] for r in summary['top_bearish']]
    })


# For local testing
if __name__ == '__main__':
    run_analysis()
