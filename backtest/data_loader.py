"""Data loading utilities for Polygon flat files."""

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, List, Literal, Optional

Timeframe = Literal["minute", "day", "auto"]


@dataclass
class Bar:
    """Represents a single OHLC bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    ticker: str = ""
    timeframe: Optional[str] = None

    def __post_init__(self):
        """Validate bar data."""
        if self.high < max(self.open, self.close, self.low):
            raise ValueError(f"High ({self.high}) must be >= max of open/close/low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError(f"Low ({self.low}) must be <= min of open/close/high")


class DataLoader:
    """Loads OHLC data from Polygon flat files."""

    @classmethod
    def from_polygon_csv(
        cls, 
        file_path: str | Path, 
        timeframe: Timeframe = "auto"
    ) -> List[Bar]:
        """
        Load OHLC data from Polygon CSV format.
        
        Expected format:
        ticker,volume,open,close,high,low,window_start,transactions
        
        Args:
            file_path: Path to the CSV file
            timeframe: Expected timeframe ("minute", "day", or "auto" to detect)
            
        Returns:
            List of Bar objects sorted by timestamp
        """
        bars = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Convert Polygon timestamp (nanoseconds since epoch) to datetime
                    timestamp_ns = int(row['window_start'])
                    timestamp = datetime.fromtimestamp(timestamp_ns / 1_000_000_000)
                    
                    bar = Bar(
                        timestamp=timestamp,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        ticker=row['ticker']
                    )
                    bars.append(bar)
                    
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping malformed row: {row}. Error: {e}")
                    continue
        
        # Sort by timestamp to ensure chronological order
        bars.sort(key=lambda x: x.timestamp)
        
        # Detect or validate timeframe
        detected_timeframe = cls._detect_timeframe(bars)
        
        if timeframe != "auto" and timeframe != detected_timeframe:
            print(f"Warning: Expected {timeframe} data but detected {detected_timeframe}")
        
        # Set timeframe on all bars
        final_timeframe = detected_timeframe if timeframe == "auto" else timeframe
        for bar in bars:
            bar.timeframe = final_timeframe
        
        print(f"Loaded {len(bars)} {final_timeframe} bars from {file_path}")
        if bars:
            print(f"Date range: {bars[0].timestamp} to {bars[-1].timestamp}")
            if detected_timeframe == "minute":
                print(f"Tickers: {len(set(bar.ticker for bar in bars))}")
            else:
                print(f"Tickers: {len(set(bar.ticker for bar in bars))}")
        
        return bars
    
    @classmethod
    def _detect_timeframe(cls, bars: List[Bar]) -> str:
        """
        Detect timeframe by analyzing timestamp gaps and patterns.
        
        Args:
            bars: List of bars sorted by timestamp
            
        Returns:
            Detected timeframe: "minute" or "day"
        """
        if len(bars) < 2:
            return "day"  # Default for single bar
        
        # Check if all bars have same timestamp (day data characteristic)
        unique_timestamps = len(set(bar.timestamp for bar in bars))
        if unique_timestamps == 1:
            return "day"
        
        # Sample gaps throughout the data, not just first few
        gaps = []
        sample_size = min(50, len(bars) - 1)
        step = max(1, len(bars) // sample_size)
        
        for i in range(step, len(bars), step):
            gap = (bars[i].timestamp - bars[i-step].timestamp).total_seconds()
            if gap > 0:  # Only count positive gaps
                gaps.append(gap)
        
        if not gaps:
            return "day"
        
        # Look for minute-like patterns (60 second gaps)
        minute_gaps = [g for g in gaps if 50 <= g <= 70]
        very_small_gaps = [g for g in gaps if g < 5]  # Sub-second gaps
        large_gaps = [g for g in gaps if g > 3600]  # > 1 hour gaps
        
        # Heuristics for classification
        if len(minute_gaps) > len(gaps) * 0.3:  # 30% of gaps are ~60 seconds
            return "minute"
        elif len(very_small_gaps) > len(gaps) * 0.3:  # Many sub-second gaps
            return "minute"
        elif len(large_gaps) > len(gaps) * 0.7:  # Mostly large gaps
            return "day"
        
        # Fallback to average gap analysis
        avg_gap = sum(gaps) / len(gaps)
        return "minute" if avg_gap < 300 else "day"

    @classmethod
    def iter_polygon_csv(
        cls, 
        file_path: str | Path, 
        timeframe: Optional[str] = None
    ) -> Iterator[Bar]:
        """
        Iterate through bars without loading all into memory.
        Useful for large datasets.
        
        Args:
            file_path: Path to the CSV file
            timeframe: Optional timeframe to set on bars
            
        Yields:
            Bar objects in file order
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Convert Polygon timestamp (nanoseconds since epoch) to datetime
                    timestamp_ns = int(row['window_start'])
                    timestamp = datetime.fromtimestamp(timestamp_ns / 1_000_000_000)
                    
                    yield Bar(
                        timestamp=timestamp,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        ticker=row['ticker'],
                        timeframe=timeframe
                    )
                    
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping malformed row: {row}. Error: {e}")
                    continue