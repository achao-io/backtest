"""Polygon flat file downloader using S3-compatible API."""

import os
import gzip
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PolygonDownloader:
    """Downloads Polygon flat files using S3-compatible API."""
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint: str = "https://files.polygon.io",
        bucket: str = "flatfiles",
        cache_dir: str = "data/downloads"
    ):
        """
        Initialize the Polygon downloader.
        
        Args:
            access_key: Polygon S3 access key (from env if None)
            secret_key: Polygon S3 secret key (from env if None)
            endpoint: Polygon S3 endpoint
            bucket: Polygon S3 bucket name
            cache_dir: Local directory for downloaded files
        """
        self.access_key = access_key or os.getenv("POLYGON_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("POLYGON_SECRET_KEY")
        self.endpoint = endpoint or os.getenv("POLYGON_ENDPOINT", "https://files.polygon.io")
        self.bucket = bucket or os.getenv("POLYGON_BUCKET", "flatfiles")
        self.cache_dir = Path(cache_dir or os.getenv("DATA_CACHE_DIR", "data/downloads"))
        
        # Validate credentials
        if not self.access_key or not self.secret_key:
            raise ValueError(
                "Polygon credentials not found. Set POLYGON_ACCESS_KEY and POLYGON_SECRET_KEY "
                "environment variables or pass them directly."
            )
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client with correct configuration for Polygon
        session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
        
        self.s3_client = session.client(
            's3',
            endpoint_url=self.endpoint,
            config=Config(signature_version='s3v4')
        )
    
    def download_stock_minute_data(
        self, 
        target_date: Union[str, date],
        force_download: bool = False
    ) -> Path:
        """
        Download minute-level stock aggregate data for all stocks on a specific date.
        
        Args:
            target_date: Date as string "YYYY-MM-DD" or date object
            force_download: Re-download even if file exists locally
            
        Returns:
            Path to the downloaded CSV file
            
        Raises:
            FileNotFoundError: If file doesn't exist on Polygon
            CredentialError: If authentication fails
        """
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        # Build S3 key: us_stocks_sip/minute_aggs_v1/year/month/year-month-day.csv.gz
        s3_key = f"us_stocks_sip/minute_aggs_v1/{target_date.year:04d}/{target_date.month:02d}/{target_date.year:04d}-{target_date.month:02d}-{target_date.day:02d}.csv.gz"
        
        # Local file path
        local_dir = self.cache_dir / "us_stocks_sip" / "minute_aggs"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file = local_dir / f"{target_date}.csv"
        
        # Check if file already exists
        if local_file.exists() and not force_download:
            print(f"✅ Using cached file: {local_file}")
            return local_file
        
        try:
            print(f"📥 Downloading US stocks minute data for {target_date}...")
            
            # Download compressed file
            compressed_file = local_file.with_suffix('.csv.gz')
            self.s3_client.download_file(self.bucket, s3_key, str(compressed_file))
            
            # Decompress
            with gzip.open(compressed_file, 'rt') as gz_file:
                with open(local_file, 'w') as csv_file:
                    csv_file.write(gz_file.read())
            
            # Remove compressed file
            compressed_file.unlink()
            
            print(f"✅ Downloaded: {local_file}")
            return local_file
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"No minute data found for {target_date}")
            elif error_code in ['AccessDenied', 'InvalidAccessKeyId']:
                raise PermissionError("Invalid Polygon credentials or insufficient permissions")
            else:
                raise RuntimeError(f"Download failed: {e}")
        except NoCredentialsError:
            raise PermissionError("Polygon credentials not configured")
    
    def download_stock_day_data(
        self, 
        target_date: Union[str, date],
        force_download: bool = False
    ) -> Path:
        """
        Download day-level stock aggregate data for all stocks on a specific date.
        
        Args:
            target_date: Date as string "YYYY-MM-DD" or date object
            force_download: Re-download even if file exists locally
            
        Returns:
            Path to the downloaded CSV file
        """
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        # Build S3 key: us_stocks_sip/day_aggs_v1/year/month/year-month-day.csv.gz
        s3_key = f"us_stocks_sip/day_aggs_v1/{target_date.year:04d}/{target_date.month:02d}/{target_date.year:04d}-{target_date.month:02d}-{target_date.day:02d}.csv.gz"
        
        # Local file path
        local_dir = self.cache_dir / "us_stocks_sip" / "day_aggs"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file = local_dir / f"{target_date}.csv"
        
        # Check if file already exists
        if local_file.exists() and not force_download:
            print(f"✅ Using cached file: {local_file}")
            return local_file
        
        try:
            print(f"📥 Downloading US stocks day data for {target_date}...")
            
            # Download compressed file
            compressed_file = local_file.with_suffix('.csv.gz')
            self.s3_client.download_file(self.bucket, s3_key, str(compressed_file))
            
            # Decompress
            with gzip.open(compressed_file, 'rt') as gz_file:
                with open(local_file, 'w') as csv_file:
                    csv_file.write(gz_file.read())
            
            # Remove compressed file
            compressed_file.unlink()
            
            print(f"✅ Downloaded: {local_file}")
            return local_file
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"No day data found for {target_date}")
            elif error_code in ['AccessDenied', 'InvalidAccessKeyId']:
                raise PermissionError("Invalid Polygon credentials or insufficient permissions")
            else:
                raise RuntimeError(f"Download failed: {e}")
    
    def list_available_dates(
        self, 
        asset_class: str = "stocks", 
        data_type: str = "minute_candlesticks",
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[str]:
        """
        List available dates for a given asset class and data type.
        
        Args:
            asset_class: Asset class (e.g., "stocks")
            data_type: Data type (e.g., "minute_candlesticks", "day_candlesticks")
            year: Filter by specific year
            month: Filter by specific month (requires year)
            
        Returns:
            List of available date prefixes
        """
        try:
            prefix = f"{asset_class}/{data_type}/"
            if year:
                prefix += f"{year:04d}/"
                if month:
                    prefix += f"{month:02d}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter='/'
            )
            
            # Extract date prefixes
            dates = []
            for obj in response.get('CommonPrefixes', []):
                date_part = obj['Prefix'].replace(prefix, '').rstrip('/')
                dates.append(date_part)
            
            return sorted(dates)
            
        except ClientError as e:
            print(f"Warning: Could not list available dates: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test connection to Polygon S3 service.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list objects in the bucket (limit to 1)
            self.s3_client.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
            print("✅ Connection to Polygon S3 successful")
            return True
        except ClientError as e:
            print(f"❌ Connection failed: {e}")
            return False
        except NoCredentialsError:
            print("❌ No credentials configured")
            return False