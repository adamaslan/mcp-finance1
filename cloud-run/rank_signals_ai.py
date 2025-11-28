"""
Cloud Function: AI Signal Ranking with Gemini
Location: option2-gcp/cloud-functions/rank_signals_ai/main.py

Triggered by: Pub/Sub topic "signals-detected"
Purpose: Use Vertex AI Gemini to rank and score all signals
"""

import base64
import json
import os
from datetime import datetime

from google.cloud import aiplatform, firestore, pubsub_v1
from vertexai.preview.generative_models import GenerativeModel

# Initialize clients
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "technical-analysis-prod")
REGION = os.getenv("GCP_REGION", "us-central1")

db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)


def rank_signals_ai(event, context):
    """
    Main Cloud Function handler
    Uses Gemini to rank signals 1-100
    """
    # Decode message
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    
    symbol = data['symbol']
    signals = data['signals']
    market_data = data['market_data']
    request_id = data.get('request_id')
    
    print(f"🤖 AI ranking {len(signals)} signals for {symbol}")
    
    try:
        # Use Gemini to rank signals
        ranked_signals = rank_with_gemini(symbol, signals, market_data)
        
        print(f"✅ AI ranked {len(ranked_signals)} signals for {symbol}")
        
        # Calculate summary
        summary = {
            "total_signals": len(ranked_signals),
            "bullish": sum(1 for s in ranked_signals if 'BULLISH' in s['strength']),
            "bearish": sum(1 for s in ranked_signals if 'BEARISH' in s['strength']),
            "avg_score": sum(s['ai_score'] for s in ranked_signals) / len(ranked_signals) if ranked_signals else 0
        }
        
        # Update Firestore with ranked signals
        result = {
            "symbol": symbol,
            "timestamp": datetime.now(),
            "price": market_data['price'],
            "change": market_data['change'],
            "signals": ranked_signals,
            "summary": summary,
            "indicators": {
                "rsi": market_data['rsi'],
                "macd": market_data['macd'],
                "adx": market_data['adx']
            },
            "ranked": True,
            "ranked_by": "gemini-2.0-flash"
        }
        
        # Save to Firestore
        db.collection("signals").document(symbol).set(result)
        
        # Also save to history
        save_to_history(symbol, result)
        
        # Publish completion event
        publish_completion(symbol, request_id)
        
        return {"status": "success", "symbol": symbol, "ranked": len(ranked_signals)}
    
    except Exception as e:
        print(f"❌ Error ranking signals for {symbol}: {e}")
        
        # Fallback to rule-based ranking
        print(f"⚠️  Falling back to rule-based ranking")
        fallback_ranking(symbol, signals, market_data, request_id)
        
        return {"status": "fallback", "symbol": symbol, "error": str(e)}


def rank_with_gemini(symbol: str, signals: list, market_data: dict) -> list:
    """Use Gemini to rank signals"""
    
    # Initialize Gemini model
    model = GenerativeModel("gemini-2.0-flash-exp")
    
    # Build prompt
    prompt = f"""You are an expert technical analyst. Score these trading signals for {symbol}.

MARKET DATA:
- Price: ${market_data['price']:.2f} | Change: {market_data['change']:.2f}%
- RSI: {market_data['rsi']:.1f} | MACD: {market_data['macd']:.4f} | ADX: {market_data['adx']:.1f}

SIGNALS TO SCORE:
"""
    
    for i, sig in enumerate(signals, 1):
        prompt += f"{i}. {sig['signal']}: {sig['desc']} [{sig['strength']}]\n"
    
    prompt += """
Score each signal from 1-100 based on:
- Actionability: Can a trader act on this signal now?
- Reliability: How historically accurate is this signal type?
- Timing: Is this signal relevant at this moment?
- Risk/Reward: What's the potential upside vs downside?

Return ONLY valid JSON (no markdown, no explanations):
{
  "scores": [
    {"signal_number": 1, "score": 85, "reasoning": "Strong momentum confirmed by volume"},
    {"signal_number": 2, "score": 72, "reasoning": "Oversold but no reversal pattern yet"}
  ]
}

Make reasoning brief (under 60 chars). Score ALL signals.
"""
    
    # Generate response
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown fences if present)
    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0].strip()
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0].strip()
    
    # Extract JSON
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        response_text = response_text[start_idx:end_idx+1]
    
    # Parse JSON
    scores_data = json.loads(response_text)
    
    # Apply scores to signals
    for score_item in scores_data.get('scores', []):
        sig_num = score_item['signal_number'] - 1
        if 0 <= sig_num < len(signals):
            signals[sig_num]['ai_score'] = score_item.get('score', 50)
            signals[sig_num]['ai_reasoning'] = score_item.get('reasoning', 'No reasoning')
    
    # Fill in any missing scores with default
    for signal in signals:
        if 'ai_score' not in signal:
            signal['ai_score'] = 50
            signal['ai_reasoning'] = 'Score not provided by AI'
    
    # Sort by score
    signals.sort(key=lambda x: x['ai_score'], reverse=True)
    
    # Add ranks
    for rank, signal in enumerate(signals, 1):
        signal['rank'] = rank
    
    return signals


def fallback_ranking(symbol: str, signals: list, market_data: dict, request_id: str):
    """Fallback to rule-based ranking if AI fails"""
    
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
        
        signal['ai_score'] = min(score, 90)
        signal['ai_reasoning'] = 'Rule-based (AI unavailable)'
    
    signals.sort(key=lambda x: x['ai_score'], reverse=True)
    
    for rank, signal in enumerate(signals, 1):
        signal['rank'] = rank
    
    # Save to Firestore
    summary = {
        "total_signals": len(signals),
        "bullish": sum(1 for s in signals if 'BULLISH' in s['strength']),
        "bearish": sum(1 for s in signals if 'BEARISH' in s['strength']),
        "avg_score": sum(s['ai_score'] for s in signals) / len(signals) if signals else 0
    }
    
    result = {
        "symbol": symbol,
        "timestamp": datetime.now(),
        "price": market_data['price'],
        "change": market_data['change'],
        "signals": signals,
        "summary": summary,
        "indicators": {
            "rsi": market_data['rsi'],
            "macd": market_data['macd'],
            "adx": market_data['adx']
        },
        "ranked": True,
        "ranked_by": "rule-based-fallback"
    }
    
    db.collection("signals").document(symbol).set(result)
    
    # Save to history
    save_to_history(symbol, result)
    
    # Publish completion
    publish_completion(symbol, request_id)


def save_to_history(symbol: str, result: dict):
    """Save analysis to historical collection"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Store in history collection
    history_ref = db.collection("analysis").document(symbol).collection("history").document(date_str)
    history_ref.set({
        "date": date_str,
        "summary": result['summary'],
        "price": result['price'],
        "change": result['change'],
        "top_signals": result['signals'][:5],  # Store top 5 only
        "timestamp": datetime.now()
    })
    
    print(f"💾 Saved to history: analysis/{symbol}/history/{date_str}")


def publish_completion(symbol: str, request_id: str):
    """Publish analysis completion event"""
    topic_path = publisher.topic_path(PROJECT_ID, "analysis-complete")
    
    message_data = {
        "symbol": symbol,
        "request_id": request_id,
        "status": "complete",
        "timestamp": datetime.now().isoformat()
    }
    
    future = publisher.publish(
        topic_path,
        data=json.dumps(message_data).encode("utf-8")
    )
    
    print(f"📤 Published analysis-complete: {future.result()}")


if __name__ == "__main__":
    # Local testing
    test_event = {
        'data': base64.b64encode(json.dumps({
            "symbol": "AAPL",
            "request_id": "test123",
            "signals": [
                {
                    "signal": "RSI OVERSOLD",
                    "desc": "RSI at 28.5",
                    "strength": "BULLISH",
                    "category": "RSI"
                },
                {
                    "signal": "MACD BULL CROSS",
                    "desc": "MACD crossed above signal",
                    "strength": "BULLISH",
                    "category": "MACD"
                }
            ],
            "market_data": {
                "price": 185.50,
                "change": 1.2,
                "rsi": 28.5,
                "macd": 0.0234,
                "adx": 32.1
            }
        }).encode('utf-8'))
    }
    
    result = rank_signals_ai(test_event, None)
    print(f"Result: {result}")