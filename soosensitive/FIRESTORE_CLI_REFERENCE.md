# Firestore CLI & Python Quick Reference

## 🔹 GCloud CLI Commands

### Database Information

```bash
# List all Firestore databases
gcloud firestore databases list --project=ttb-lang1

# Get details about default database
gcloud firestore databases describe --project=ttb-lang1 \
  --database='(default)'

# List backups
gcloud firestore backups list --project=ttb-lang1

# Recent operations
gcloud firestore operations list --project=ttb-lang1 --limit=20
```

### Indexes

```bash
# List composite indexes
gcloud firestore indexes composite list --project=ttb-lang1

# Describe a specific index
gcloud firestore indexes composite describe <INDEX_ID> --project=ttb-lang1

# Create a new composite index (if needed)
gcloud firestore indexes composite create --project=ttb-lang1 \
  --collection-id=options_chains \
  --field-config=field-path=strike,order=ASCENDING \
  --field-config=field-path=expiration_date,order=DESCENDING
```

### Locations

```bash
# List available locations for Firestore
gcloud firestore locations list
```

---

## 🔹 Firebase CLI Commands

### Install Firebase CLI

```bash
# If not already installed
npm install -g firebase-tools

# Verify installation
firebase --version
```

### Database Operations

```bash
# Initialize Firebase in current project
firebase init firestore

# Emulator commands (local testing)
firebase emulators:start --project=ttb-lang1

# View Firestore data (via console)
firebase open firestore --project=ttb-lang1
```

---

## 🔹 Python Google Cloud Library

### Installation

```bash
# Install required packages (via mamba)
mamba activate fin-ai1
pip install google-cloud-firestore

# Or add to environment.yml
echo "google-cloud-firestore" >> requirements.txt
```

### Connect to Firestore

```python
from google.cloud import firestore

# Default project (from gcloud config)
db = firestore.Client()

# Specific project
db = firestore.Client(project="ttb-lang1")
```

### Read Operations

```python
# Get single document
doc = db.collection("options_chains").document("AEM").get()
if doc.exists:
    print(doc.to_dict())

# Get all documents in collection
docs = db.collection("options_chains").stream()
for doc in docs:
    print(f"{doc.id}: {doc.to_dict()}")

# Query with filters
query = db.collection("options_quotes")\
    .where("current", ">", 200)\
    .stream()

for doc in query:
    print(doc.to_dict())

# Get sub-collection documents
expirations = db.collection("options_chains")\
    .document("AEM")\
    .collection("expirations")\
    .stream()

# Limit results
docs = db.collection("options_chains").limit(10).stream()

# Order results
docs = db.collection("options_chains")\
    .order_by("last_trade_price", direction=firestore.Query.DESCENDING)\
    .stream()
```

### Write Operations

```python
# Set (create or overwrite)
db.collection("test").document("doc1").set({
    "name": "Test",
    "value": 123
})

# Add (auto-generate ID)
doc_ref = db.collection("test").add({
    "name": "Auto ID",
    "timestamp": firestore.SERVER_TIMESTAMP
})

# Update (partial update)
db.collection("test").document("doc1").update({
    "status": "updated",
    "timestamp": firestore.SERVER_TIMESTAMP
})

# Batch write (multiple operations)
batch = db.batch()

batch.set(db.collection("test").document("doc1"), {"field": "value1"})
batch.update(db.collection("test").document("doc2"), {"field": "value2"})
batch.delete(db.collection("test").document("doc3"))

batch.commit()
```

### Delete Operations

```python
# Delete document
db.collection("test").document("doc1").delete()

# Delete field from document
db.collection("test").document("doc1").update({
    "field_to_delete": firestore.DELETE_FIELD
})

# Delete entire collection (batch)
docs = db.collection("test").stream()
for doc in docs:
    doc.reference.delete()
```

### Transaction Example

```python
@db.transaction
def update_with_transaction(transaction, symbol, new_price):
    doc_ref = db.collection("options_quotes").document(symbol)
    doc = doc_ref.get(transaction=transaction)

    if doc.exists:
        transaction.update(doc_ref, {"current": new_price})

# Call transaction
db.transaction(lambda tx: update_with_transaction(tx, "AEM", 215.50))
```

### Batch Operations

```python
# Large batch write (handles limits automatically)
def batch_write_large(docs_to_write):
    batch = db.batch()
    batch_count = 0

    for doc_id, doc_data in docs_to_write.items():
        batch.set(
            db.collection("large_data").document(doc_id),
            doc_data
        )
        batch_count += 1

        if batch_count >= 450:  # Firestore batch limit
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

# Usage
batch_write_large({
    "doc1": {"data": "value1"},
    "doc2": {"data": "value2"},
})
```

---

## 🔹 Query Examples for Finnhub Pipeline

### Get Options Chain for Symbol

```python
# Get AEM options chain metadata
symbol = "AEM"
chain = db.collection("options_chains").document(symbol).get().to_dict()

print(f"{symbol}: {chain['total_calls']} calls, {chain['total_puts']} puts")
print(f"Expirations: {chain['num_expirations']}")
print(f"Last trade price: ${chain['last_trade_price']}")
```

### Get All Expirations for Symbol

```python
# Get all expiration dates for AEM
symbol = "AEM"
expirations = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .stream()

for exp in expirations:
    exp_data = exp.to_dict()
    print(f"{exp.id}: IV={exp_data['implied_volatility']:.2f}%, "
          f"Call Vol={exp_data['call_volume']}, "
          f"Put Vol={exp_data['put_volume']}")
```

### Get Calls for Specific Strike & Expiration

```python
# Get AEM 2026-02-13 $160 call
symbol = "AEM"
expiration = "2026-02-13"
strike = "160"

call = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .collection("calls")\
    .document(strike)\
    .get()

if call.exists:
    call_data = call.to_dict()
    print(f"Strike: ${call_data['strike']}")
    print(f"Last Price: ${call_data['last_price']}")
    print(f"IV: {call_data['implied_volatility']:.2f}%")
    print(f"Delta: {call_data['delta']:.4f}")
```

### Get Current Quote

```python
# Get latest quote for AEM
symbol = "AEM"
quote = db.collection("options_quotes").document(symbol).get().to_dict()

print(f"{symbol}: ${quote['current']}")
print(f"Change: {quote['change']:+.2f} ({quote['change_percent']:+.2f}%)")
print(f"OHLC: {quote['open']} / {quote['high']} / {quote['low']} / {quote['close']}")
```

### Get Historical Candles

```python
# Get 1-day candles for AEM
symbol = "AEM"
interval = "1day"

candle_doc = db.collection("candle_data")\
    .document(symbol)\
    .collection("intervals")\
    .document(interval)\
    .get()

candle_data = candle_doc.to_dict()
print(f"Status: {candle_data['status']}")
print(f"Source: {candle_data['source']}")
print(f"Number of candles: {candle_data['num_candles']}")

# Iterate through candles
for candle in candle_data['candles']:
    print(f"{candle['datetime']}: "
          f"O={candle['open']:.2f}, "
          f"H={candle['high']:.2f}, "
          f"L={candle['low']:.2f}, "
          f"C={candle['close']:.2f}, "
          f"V={candle['volume']:,}")
```

### Get Latest Pipeline Run

```python
# Get most recent pipeline run
runs = db.collection("pipeline_runs")\
    .order_by("created_at", direction=firestore.Query.DESCENDING)\
    .limit(1)\
    .stream()

for run in runs:
    run_data = run.to_dict()
    print(f"Run: {run.id}")
    print(f"Status: {run_data['status']}")
    print(f"Symbols: {', '.join(run_data['symbols'])}")
    print(f"Elapsed: {run_data['elapsed_seconds']:.1f}s")

    # Check results per symbol
    for symbol, result in run_data['results'].items():
        print(f"  {symbol}: {result['options_chain'].get('status')}")
```

### Query Puts with Strike Price Filter

```python
# Get all puts for AEM 2026-02-13 above/below certain strike
symbol = "AEM"
expiration = "2026-02-13"
strike_threshold = 170

puts = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .collection("puts")\
    .stream()

for put in puts:
    put_data = put.to_dict()
    strike = float(put_data['strike'])

    if strike > strike_threshold:
        print(f"Strike ${strike:.2f}: IV={put_data['implied_volatility']:.2f}%, "
              f"Price=${put_data['last_price']:.2f}")
```

---

## 🔹 Monitoring & Debugging

### Check Authentication

```python
from google.cloud import firestore
import google.auth

# Get current credentials
credentials, project = google.auth.default()
print(f"Project: {project}")
print(f"Credentials: {credentials}")

# Test connection
db = firestore.Client(project="ttb-lang1")
doc = db.collection("_health_check").document("test").get()
print(f"Connection: {'✅ OK' if doc.exists else '❌ Failed'}")
```

### Count Documents in Collection

```python
# Count all documents
def count_collection(collection_name):
    docs = db.collection(collection_name).stream()
    return sum(1 for _ in docs)

count = count_collection("options_chains")
print(f"Total documents: {count}")
```

### Get Collection Size

```python
# Estimate total size (rough)
def estimate_collection_size(collection_name):
    docs = db.collection(collection_name).stream()
    total_size = 0

    for doc in docs:
        import json
        doc_size = len(json.dumps(doc.to_dict()).encode('utf-8'))
        total_size += doc_size

    return total_size / (1024 * 1024)  # Convert to MB

size_mb = estimate_collection_size("options_chains")
print(f"Estimated size: {size_mb:.2f} MB")
```

### Listen for Real-time Updates

```python
# Listen to specific document changes
def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        print(f"{change.type.name}: {change.document.id}")
        print(change.document.to_dict())

# Subscribe to changes
db.collection("options_quotes").document("AEM").on_snapshot(on_snapshot)

# Keep script alive to receive updates
import time
while True:
    time.sleep(1)
```

---

## 🔹 Common Troubleshooting

### Error: "not found: This document does not exist"
```python
# Check if document exists before accessing
doc = db.collection("options_chains").document("INVALID").get()
if doc.exists:
    print(doc.to_dict())
else:
    print("Document not found")
```

### Error: "PERMISSION_DENIED"
```bash
# Re-authenticate
gcloud auth application-default login

# Or check current auth
gcloud auth list
gcloud config get-value project
```

### Error: "Service Unavailable"
```python
# Implement retry logic
from google.api_core.retry import Retry
import google.api_core.gapic_v1.client_info

def query_with_retry(collection_name):
    try:
        docs = db.collection(collection_name).stream()
        return list(docs)
    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(2)
        return query_with_retry(collection_name)
```

### Large Result Sets Timeout
```python
# Paginate results
def paginate_collection(collection_name, page_size=100):
    query = db.collection(collection_name).limit(page_size)
    last_doc = None

    while True:
        docs = list(query.stream())
        if not docs:
            break

        for doc in docs:
            yield doc

        last_doc = docs[-1]
        query = db.collection(collection_name)\
            .start_after(last_doc)\
            .limit(page_size)

# Usage
for doc in paginate_collection("options_chains"):
    print(doc.id)
```

---

## 📞 References

- **GCloud Firestore Docs**: https://cloud.google.com/firestore/docs
- **Python Client Library**: https://googleapis.dev/python/firestore/latest/
- **Firebase Console**: https://console.firebase.google.com/project/ttb-lang1
- **GCloud CLI Docs**: https://cloud.google.com/sdk/gcloud/reference/firestore

---

## 💡 Quick Tips

1. **Always check if document exists** before calling `to_dict()`
2. **Use batch operations** for writing multiple documents (faster)
3. **Limit queries** to prevent timeout on large collections
4. **Use indexes** for complex queries (Firestore auto-suggests them)
5. **Test queries locally** before deploying to production
6. **Monitor free tier usage** (50k reads/day free)

---

**Generated**: 2026-02-11
**Project**: ttb-lang1
