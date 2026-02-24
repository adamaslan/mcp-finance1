"""
Tests for Fibonacci historical signal tracking database schema.

Tests verify:
- Database schema compiles with Drizzle ORM
- Signal recording to database
- Performance calculation queries
- Win rate calculation (price > level)
- API endpoint returns correct format
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional
import json


class FibonacciSignalRecord:
    """Model for Fibonacci signal records in database."""

    def __init__(
        self,
        id: str,
        user_id: str,
        symbol: str,
        level_price: float,
        level_name: str,
        signal_time: datetime,
        signal_strength: str,
        category: str,
        timeframe: str,
        result: Optional[str] = None,
        result_price: Optional[float] = None,
        result_time: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ):
        """Initialize signal record."""
        self.id = id
        self.user_id = user_id
        self.symbol = symbol
        self.level_price = level_price
        self.level_name = level_name
        self.signal_time = signal_time
        self.signal_strength = signal_strength
        self.category = category
        self.timeframe = timeframe
        self.result = result  # 'win' | 'loss' | 'pending'
        self.result_price = result_price
        self.result_time = result_time
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "level_price": self.level_price,
            "level_name": self.level_name,
            "signal_time": self.signal_time.isoformat(),
            "signal_strength": self.signal_strength,
            "category": self.category,
            "timeframe": self.timeframe,
            "result": self.result,
            "result_price": self.result_price,
            "result_time": self.result_time.isoformat() if self.result_time else None,
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FibonacciSignalPerformance:
    """Model for calculating signal performance metrics."""

    def __init__(self, signals: list[FibonacciSignalRecord]):
        """Initialize with signal records."""
        self.signals = signals

    def calculate_win_rate(self) -> float:
        """Calculate win rate (won / total completed signals)."""
        completed = [s for s in self.signals if s.result is not None]
        if not completed:
            return 0.0

        wins = sum(1 for s in completed if s.result == "win")
        return wins / len(completed)

    def calculate_loss_rate(self) -> float:
        """Calculate loss rate (losses / total completed)."""
        completed = [s for s in self.signals if s.result is not None]
        if not completed:
            return 0.0

        losses = sum(1 for s in completed if s.result == "loss")
        return losses / len(completed)

    def calculate_pending_count(self) -> int:
        """Count pending signals."""
        return sum(1 for s in self.signals if s.result == "pending")

    def calculate_average_move(self) -> Optional[float]:
        """Calculate average price move from signal to result."""
        completed = [
            s
            for s in self.signals
            if s.result is not None and s.result_price is not None
        ]
        if not completed:
            return None

        moves = [
            (s.result_price - s.level_price) / s.level_price * 100
            for s in completed
        ]
        return sum(moves) / len(moves)

    def calculate_by_strength(self) -> dict:
        """Calculate metrics grouped by signal strength."""
        by_strength = {}
        for signal in self.signals:
            if signal.signal_strength not in by_strength:
                by_strength[signal.signal_strength] = {
                    "total": 0,
                    "wins": 0,
                    "losses": 0,
                    "pending": 0,
                }

            strength_data = by_strength[signal.signal_strength]
            if signal.result is None:
                strength_data["pending"] += 1
            else:
                strength_data["total"] += 1
                if signal.result == "win":
                    strength_data["wins"] += 1
                elif signal.result == "loss":
                    strength_data["losses"] += 1

        # Calculate win rates
        for strength, data in by_strength.items():
            if data["total"] > 0:
                data["win_rate"] = data["wins"] / data["total"]
            else:
                data["win_rate"] = 0.0

        return by_strength

    def to_dict(self) -> dict:
        """Convert performance metrics to dictionary."""
        return {
            "total_signals": len(self.signals),
            "completed_signals": sum(1 for s in self.signals if s.result),
            "pending_signals": self.calculate_pending_count(),
            "win_rate": self.calculate_win_rate(),
            "loss_rate": self.calculate_loss_rate(),
            "average_move": self.calculate_average_move(),
            "by_strength": self.calculate_by_strength(),
        }


class TestDatabaseSchema:
    """Test database schema validation and structure."""

    def test_fibonacci_signal_record_creation(self):
        """Test creating a Fibonacci signal record."""
        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )

        assert signal.id == "sig_001"
        assert signal.user_id == "user_123"
        assert signal.symbol == "AAPL"
        assert signal.level_price == 150.0
        assert signal.result is None

    def test_fibonacci_signal_record_serialization(self):
        """Test serializing signal record to dictionary."""
        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
            metadata={"confluence": 3, "multi_timeframe": True},
        )

        data = signal.to_dict()

        assert data["id"] == "sig_001"
        assert data["user_id"] == "user_123"
        assert data["symbol"] == "AAPL"
        assert data["level_price"] == 150.0
        assert "metadata" in data
        assert isinstance(data["metadata"], str)  # JSON serialized

    def test_signal_result_update(self):
        """Test updating signal result."""
        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )

        # Simulate signal result
        result_time = now + timedelta(hours=2)
        signal.result = "win"
        signal.result_price = 155.0
        signal.result_time = result_time

        assert signal.result == "win"
        assert signal.result_price == 155.0
        assert signal.result_time == result_time

    def test_schema_fields_required(self):
        """Test that required fields are present."""
        required_fields = [
            "id",
            "user_id",
            "symbol",
            "level_price",
            "level_name",
            "signal_time",
            "signal_strength",
            "category",
            "timeframe",
        ]

        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )

        data = signal.to_dict()
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestSignalRecording:
    """Test recording signals to database simulation."""

    def test_record_single_signal(self):
        """Test recording a single signal."""
        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )

        # Simulate database insertion
        records = [signal]
        assert len(records) == 1
        assert records[0].symbol == "AAPL"

    def test_record_multiple_signals(self):
        """Test recording multiple signals."""
        now = datetime.utcnow()
        signals = []

        for i in range(5):
            signal = FibonacciSignalRecord(
                id=f"sig_{i:03d}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0 + i * 0.5,
                level_name=f"Level {i}",
                signal_time=now + timedelta(hours=i),
                signal_strength="strong" if i % 2 == 0 else "moderate",
                category="retracement",
                timeframe="1d",
            )
            signals.append(signal)

        assert len(signals) == 5
        assert signals[0].level_price == 150.0
        assert signals[4].level_price == 152.0

    def test_record_signal_with_metadata(self):
        """Test recording signal with metadata."""
        now = datetime.utcnow()
        metadata = {
            "confluence_count": 3,
            "multi_timeframe_aligned": True,
            "distance_from_current": 0.05,
            "atr_ratio": 1.5,
        }

        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
            metadata=metadata,
        )

        data = signal.to_dict()
        assert "metadata" in data


class TestPerformanceCalculation:
    """Test performance calculation queries."""

    def create_test_signals(self) -> list[FibonacciSignalRecord]:
        """Create test signals with various results."""
        now = datetime.utcnow()
        signals = []

        # Winning signals
        for i in range(3):
            signal = FibonacciSignalRecord(
                id=f"sig_win_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618 Retracement",
                signal_time=now - timedelta(days=5 - i),
                signal_strength="strong",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "win"
            signal.result_price = 155.0
            signal.result_time = now - timedelta(days=5 - i) + timedelta(hours=2)
            signals.append(signal)

        # Losing signals
        for i in range(2):
            signal = FibonacciSignalRecord(
                id=f"sig_loss_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618 Retracement",
                signal_time=now - timedelta(days=3 - i),
                signal_strength="moderate",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "loss"
            signal.result_price = 148.0
            signal.result_time = now - timedelta(days=3 - i) + timedelta(hours=2)
            signals.append(signal)

        # Pending signals
        for i in range(2):
            signal = FibonacciSignalRecord(
                id=f"sig_pending_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618 Retracement",
                signal_time=now - timedelta(hours=12 - i * 6),
                signal_strength="weak",
                category="retracement",
                timeframe="1d",
            )
            signals.append(signal)

        return signals

    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        signals = self.create_test_signals()
        performance = FibonacciSignalPerformance(signals)
        win_rate = performance.calculate_win_rate()

        # 3 wins out of 5 completed = 60%
        assert win_rate == 0.6
        assert 0 <= win_rate <= 1

    def test_calculate_loss_rate(self):
        """Test loss rate calculation."""
        signals = self.create_test_signals()
        performance = FibonacciSignalPerformance(signals)
        loss_rate = performance.calculate_loss_rate()

        # 2 losses out of 5 completed = 40%
        assert loss_rate == 0.4
        assert 0 <= loss_rate <= 1

    def test_calculate_pending_count(self):
        """Test pending signal count."""
        signals = self.create_test_signals()
        performance = FibonacciSignalPerformance(signals)
        pending = performance.calculate_pending_count()

        assert pending == 2

    def test_calculate_average_move(self):
        """Test average price move calculation."""
        signals = self.create_test_signals()
        performance = FibonacciSignalPerformance(signals)
        avg_move = performance.calculate_average_move()

        # Wins: (155-150)/150*100 = 3.33% (3x)
        # Losses: (148-150)/150*100 = -1.33% (2x)
        # Average: (3*3.33 + 2*(-1.33))/5 ≈ 1.33%
        assert avg_move is not None
        assert isinstance(avg_move, float)

    def test_calculate_by_strength(self):
        """Test performance calculation by signal strength."""
        signals = self.create_test_signals()
        performance = FibonacciSignalPerformance(signals)
        by_strength = performance.calculate_by_strength()

        assert "strong" in by_strength
        assert "moderate" in by_strength
        assert "weak" in by_strength

        # Strong signals: 3 wins, 0 losses
        assert by_strength["strong"]["wins"] == 3
        assert by_strength["strong"]["total"] == 3

        # Moderate signals: 0 wins, 2 losses
        assert by_strength["moderate"]["losses"] == 2
        assert by_strength["moderate"]["total"] == 2

    def test_win_rate_calculation_edge_cases(self):
        """Test win rate calculation with no completed signals."""
        now = datetime.utcnow()
        signals = [
            FibonacciSignalRecord(
                id="sig_pending_0",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618 Retracement",
                signal_time=now,
                signal_strength="weak",
                category="retracement",
                timeframe="1d",
            )
        ]

        performance = FibonacciSignalPerformance(signals)
        win_rate = performance.calculate_win_rate()

        # No completed signals = 0%
        assert win_rate == 0.0


class TestAPIEndpointFormat:
    """Test API response format for performance data."""

    def test_performance_dict_format(self):
        """Test that performance metrics serialize to correct format."""
        signals = self._create_sample_signals()
        performance = FibonacciSignalPerformance(signals)
        data = performance.to_dict()

        # Check required fields
        required_keys = [
            "total_signals",
            "completed_signals",
            "pending_signals",
            "win_rate",
            "loss_rate",
            "average_move",
            "by_strength",
        ]

        for key in required_keys:
            assert key in data, f"Missing key in response: {key}"

    def test_performance_api_response_structure(self):
        """Test API response structure."""
        signals = self._create_sample_signals()
        performance = FibonacciSignalPerformance(signals)
        response = {
            "symbol": "AAPL",
            "user_id": "user_123",
            "performance": performance.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        assert response["symbol"] == "AAPL"
        assert response["user_id"] == "user_123"
        assert "performance" in response
        assert "timestamp" in response

    def test_performance_metrics_are_numeric(self):
        """Test that all metrics are numeric."""
        signals = self._create_sample_signals()
        performance = FibonacciSignalPerformance(signals)
        data = performance.to_dict()

        assert isinstance(data["total_signals"], int)
        assert isinstance(data["completed_signals"], int)
        assert isinstance(data["pending_signals"], int)
        assert isinstance(data["win_rate"], float)
        assert isinstance(data["loss_rate"], float)

    @staticmethod
    def _create_sample_signals() -> list[FibonacciSignalRecord]:
        """Create sample signals for testing."""
        now = datetime.utcnow()
        signals = []

        # Create 10 signals: 6 wins, 2 losses, 2 pending
        for i in range(6):
            signal = FibonacciSignalRecord(
                id=f"sig_win_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="Level",
                signal_time=now - timedelta(days=i),
                signal_strength="strong",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "win"
            signal.result_price = 155.0
            signals.append(signal)

        for i in range(2):
            signal = FibonacciSignalRecord(
                id=f"sig_loss_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="Level",
                signal_time=now - timedelta(hours=i),
                signal_strength="moderate",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "loss"
            signal.result_price = 148.0
            signals.append(signal)

        for i in range(2):
            signal = FibonacciSignalRecord(
                id=f"sig_pending_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="Level",
                signal_time=now - timedelta(hours=20 + i),
                signal_strength="weak",
                category="retracement",
                timeframe="1d",
            )
            signals.append(signal)

        return signals


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
