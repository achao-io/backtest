"""Tests for the data loader module."""

import pytest
from datetime import datetime
from pathlib import Path
from backtest.data_loader import DataLoader, Bar


class TestBar:
    """Test the Bar dataclass."""
    
    def test_valid_bar_creation(self):
        """Test creating a valid bar."""
        bar = Bar(
            timestamp=datetime(2024, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000,
            ticker="SPY"
        )
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 95.0
        assert bar.close == 102.0
        assert bar.volume == 1000
        assert bar.ticker == "SPY"
    
    def test_bar_validation_high_too_low(self):
        """Test that high must be >= max(open, close, low)."""
        with pytest.raises(ValueError, match="High.*must be"):
            Bar(
                timestamp=datetime.now(),
                open=100.0,
                high=90.0,  # Invalid: high < open
                low=95.0,
                close=102.0,
                volume=1000
            )
    
    def test_bar_validation_low_too_high(self):
        """Test that low must be <= min(open, close, high)."""
        # This will actually trigger the high validation first since low=110 > high=105
        with pytest.raises(ValueError, match="High.*must be"):
            Bar(
                timestamp=datetime.now(),
                open=100.0,
                high=105.0,
                low=110.0,  # Invalid: low > high
                close=102.0,
                volume=1000
            )


class TestDataLoader:
    """Test the DataLoader class."""
    
    def test_load_sample_data(self):
        """Test loading the sample Polygon data file."""
        data = DataLoader.from_polygon_csv('data/stocks_minute_candlesticks_example.csv')
        
        # Basic checks
        assert len(data) > 0, "Should load some data"
        assert all(isinstance(bar, Bar) for bar in data), "All items should be Bar objects"
        
        # Check first bar properties
        first_bar = data[0]
        assert first_bar.ticker == 'MSFT', "Should have correct ticker"
        assert first_bar.volume > 0, "Volume should be positive"
        assert first_bar.open > 0, "Price should be positive"
        assert first_bar.high >= first_bar.open, "High should be >= open"
        assert first_bar.low <= first_bar.open, "Low should be <= open"
        
        # Check data is sorted by timestamp
        timestamps = [bar.timestamp for bar in data]
        assert timestamps == sorted(timestamps), "Data should be sorted by timestamp"
    
    def test_file_not_found(self):
        """Test handling of missing files."""
        with pytest.raises(FileNotFoundError):
            DataLoader.from_polygon_csv('nonexistent.csv')
    
    def test_iter_polygon_csv(self):
        """Test the iterator interface."""
        bars_list = list(DataLoader.iter_polygon_csv('data/stocks_minute_candlesticks_example.csv'))
        bars_loaded = DataLoader.from_polygon_csv('data/stocks_minute_candlesticks_example.csv')
        
        # Should get same number of bars
        assert len(bars_list) == len(bars_loaded)
        
        # All bars should be present (order might differ due to sorting)
        loaded_timestamps = {bar.timestamp for bar in bars_loaded}
        iter_timestamps = {bar.timestamp for bar in bars_list}
        assert loaded_timestamps == iter_timestamps
    
    @pytest.mark.parametrize("field,value", [
        ("open", "invalid"),
        ("high", ""),
        ("low", "not_a_number"),
        ("close", "abc"),
        ("volume", "xyz"),
        ("window_start", "not_timestamp"),
    ])
    def test_malformed_data_handling(self, tmp_path, field, value):
        """Test handling of malformed CSV data."""
        # Create a test CSV with malformed data
        test_csv = tmp_path / "malformed.csv"
        test_csv.write_text(
            "ticker,volume,open,close,high,low,window_start,transactions\n"
            f"TEST,1000,100.0,101.0,102.0,99.0,{value if field == 'window_start' else '1704096000000000000'},10\n"
            if field != "window_start" else
            "ticker,volume,open,close,high,low,window_start,transactions\n"
            f"TEST,{value if field == 'volume' else '1000'},{value if field == 'open' else '100.0'},"
            f"{value if field == 'close' else '101.0'},{value if field == 'high' else '102.0'},"
            f"{value if field == 'low' else '99.0'},1704096000000000000,10\n"
        )
        
        # Should not crash but may return empty list
        data = DataLoader.from_polygon_csv(test_csv)
        # Malformed rows should be skipped
        assert isinstance(data, list)