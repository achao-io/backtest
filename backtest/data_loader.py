"""Data loading utilities for Polygon flat files."""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, List


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

    def __post_init__(self):
        """Validate bar data."""
        if self.high < max(self.open, self.close, self.low):
            raise ValueError(f"High ({self.high}) must be >= max of open/close/low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError(f"Low ({self.low}) must be <= min of open/close/high")


class DataLoader:
    """Loads OHLC data from Polygon flat files."""

    @classmethod
    def from_polygon_csv(cls, file_path: str | Path) -> List[Bar]:
        """
        Load minute OHLC data from Polygon CSV format.
        
        Expected format:
        ticker,volume,open,close,high,low,window_start,transactions
        
        Args:
            file_path: Path to the CSV file
            
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
        
        print(f"Loaded {len(bars)} bars from {file_path}")
        if bars:
            print(f"Date range: {bars[0].timestamp} to {bars[-1].timestamp}")
        
        return bars

    @classmethod
    def iter_polygon_csv(cls, file_path: str | Path) -> Iterator[Bar]:
        """
        Iterate through bars without loading all into memory.
        Useful for large datasets.
        
        Args:
            file_path: Path to the CSV file
            
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
                        ticker=row['ticker']
                    )
                    
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping malformed row: {row}. Error: {e}")
                    continue