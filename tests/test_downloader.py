"""Tests for the Polygon downloader module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from backtest.downloader import PolygonDownloader


class TestPolygonDownloader:
    """Test the PolygonDownloader class."""

    def test_init_with_env_credentials(self):
        """Test initialization with environment credentials."""
        with patch.dict(
            "os.environ",
            {
                "POLYGON_ACCESS_KEY": "test_access_key",
                "POLYGON_SECRET_KEY": "test_secret_key",
            },
        ):
            downloader = PolygonDownloader()
            assert downloader.access_key == "test_access_key"
            assert downloader.secret_key == "test_secret_key"
            assert downloader.endpoint == "https://files.polygon.io"
            assert downloader.bucket == "flatfiles"

    def test_init_with_explicit_credentials(self):
        """Test initialization with explicit credentials."""
        downloader = PolygonDownloader(
            access_key="explicit_access",
            secret_key="explicit_secret",
            endpoint="https://custom.endpoint.com",
            bucket="custom_bucket",
        )
        assert downloader.access_key == "explicit_access"
        assert downloader.secret_key == "explicit_secret"
        assert downloader.endpoint == "https://custom.endpoint.com"
        assert downloader.bucket == "custom_bucket"

    def test_init_missing_credentials(self):
        """Test that missing credentials raise ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="Polygon credentials not found"):
                PolygonDownloader()

    @patch("backtest.downloader.boto3.Session")
    def test_s3_client_initialization(self, mock_session):
        """Test S3 client is initialized correctly."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        # Create downloader to trigger S3 client initialization
        _downloader = PolygonDownloader(
            access_key="test_key", secret_key="test_secret"
        )

        # Verify session creation
        mock_session.assert_called_once_with(
            aws_access_key_id="test_key", aws_secret_access_key="test_secret"
        )

        # Verify client creation
        mock_session.return_value.client.assert_called_once()

    @patch("backtest.downloader.boto3.Session")
    def test_test_connection_success(self, mock_session):
        """Test successful connection test."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.list_objects_v2.return_value = {"Contents": []}

        downloader = PolygonDownloader(access_key="test_key", secret_key="test_secret")

        result = downloader.test_connection()

        assert result is True
        mock_client.list_objects_v2.assert_called_once_with(
            Bucket="flatfiles", MaxKeys=1
        )

    @patch("backtest.downloader.boto3.Session")
    def test_test_connection_failure(self, mock_session):
        """Test connection test failure."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "list_objects_v2"
        )

        downloader = PolygonDownloader(access_key="test_key", secret_key="test_secret")

        result = downloader.test_connection()

        assert result is False

    @patch("backtest.downloader.gzip.open")
    @patch("backtest.downloader.boto3.Session")
    @patch("pathlib.Path.unlink")
    def test_download_stock_day_data(self, mock_unlink, mock_session, mock_gzip):
        """Test downloading day data."""
        # Setup mocks
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        # Mock gzip decompression
        mock_gzip.return_value.__enter__.return_value.read.return_value = (
            "test,csv,data"
        )

        downloader = PolygonDownloader(
            access_key="test_key", secret_key="test_secret", cache_dir="test_cache"
        )

        # Mock successful download
        with patch("builtins.open", create=True) as _:
            result = downloader.download_stock_day_data("2024-08-07")

            # Verify S3 download was called
            mock_client.download_file.assert_called_once()
            args = mock_client.download_file.call_args[0]
            assert args[0] == "flatfiles"  # bucket
            assert (
                "us_stocks_sip/day_aggs_v1/2024/08/2024-08-07.csv.gz" in args[1]
            )  # key

            # Verify compressed file was deleted
            mock_unlink.assert_called_once()

            # Verify result
            assert isinstance(result, Path)
            assert "2024-08-07.csv" in str(result)

    @patch("backtest.downloader.boto3.Session")
    def test_download_file_not_found(self, mock_session):
        """Test handling of file not found."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "download_file"
        )

        downloader = PolygonDownloader(access_key="test_key", secret_key="test_secret")

        with pytest.raises(FileNotFoundError, match="No day data found"):
            downloader.download_stock_day_data("2024-01-01")

    @patch("backtest.downloader.boto3.Session")
    def test_download_permission_error(self, mock_session):
        """Test handling of permission errors."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "download_file"
        )

        downloader = PolygonDownloader(access_key="test_key", secret_key="test_secret")

        with pytest.raises(PermissionError, match="Invalid Polygon credentials"):
            downloader.download_stock_day_data("2024-01-01")

    def test_cache_directory_creation(self):
        """Test that cache directory is created."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test_cache"
            
            # Create downloader which should create the cache directory
            _downloader = PolygonDownloader(
                access_key="test_key",
                secret_key="test_secret", 
                cache_dir=str(cache_path)
            )
            
            assert cache_path.exists()
            assert cache_path.is_dir()
