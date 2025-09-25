"""
Nifty Indices Tracker - A CLI tool for tracking and visualizing Nifty indices data
"""

import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path


class NiftyIndicesTracker:
    """Main class for fetching and processing Nifty indices data"""

    BASE_URL = "https://www.niftyindices.com/Backpage.aspx/getHistoricaldataDBtoString"

    def __init__(self):
        self.indices_map = self._load_indices_map()
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Setup session with required headers"""
        self.session.headers.update({
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.niftyindices.com',
            'Referer': 'https://www.niftyindices.com/market-data/advanced-charting'
        })

    def _load_indices_map(self) -> Dict[str, str]:
        """Load indices names from indices-list.csv"""
        indices_map = {}
        indices_file = Path(__file__).parent.parent / 'config' / 'indices-list.csv'

        if indices_file.exists():
            df = pd.read_csv(indices_file)
            for _, row in df.iterrows():
                index_id = str(row['index_id'])
                index_name = row['index_name']
                if pd.notna(index_name) and index_name.strip():  # Only add non-empty names
                    indices_map[index_name.lower()] = index_name
                    indices_map[index_id] = index_name

        return indices_map

    def list_indices(self) -> List[str]:
        """Return list of available indices"""
        unique_indices = set()
        for key, value in self.indices_map.items():
            if not key.isdigit():  # Only add the actual names, not numbers
                unique_indices.add(value)
        return sorted(list(unique_indices))

    def find_index_name(self, search_term: str) -> Optional[str]:
        """Find exact index name from search term"""
        search_term = search_term.strip()

        # Direct match
        if search_term in self.indices_map:
            return self.indices_map[search_term]

        # Case insensitive match
        search_lower = search_term.lower()
        if search_lower in self.indices_map:
            return self.indices_map[search_lower]

        # Partial match
        for key, value in self.indices_map.items():
            if search_lower in key.lower():
                return value

        return None

    def fetch_historical_data(self, index_name: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a given index

        Args:
            index_name: Name of the index
            start_date: Start date in DD-MMM-YYYY format (e.g., '21-Jun-2025')
            end_date: End date in DD-MMM-YYYY format (e.g., '21-Sep-2025')

        Returns:
            DataFrame with historical data or None if failed
        """

        # Find the exact index name
        exact_name = self.find_index_name(index_name)
        if not exact_name:
            raise ValueError(f"Index '{index_name}' not found. Use list_indices() to see available indices.")

        payload = {
            "cinfo": json.dumps({
                'name': exact_name,
                'startDate': start_date,
                'endDate': end_date,
                'historicaltype': '1',
                'DataType': 'HR'
            })
        }

        try:
            response = self.session.post(self.BASE_URL, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'd' not in data:
                raise ValueError("Invalid response format")

            # Parse the response data
            raw_data = data['d']

            # Handle different response formats
            json_data = raw_data
            if raw_data.startswith('-1.1\n'):
                json_data = raw_data[5:]  # Remove the '-1.1\n' prefix
            elif '\n[' in raw_data:
                # Find the start of JSON array after any prefix
                json_start = raw_data.find('[')
                if json_start != -1:
                    json_data = raw_data[json_start:]

            historical_data = json.loads(json_data)

            if not historical_data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(historical_data)

            # Clean and process the data
            df = self._process_dataframe(df, exact_name)

            return df

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

        return None

    def _process_dataframe(self, df: pd.DataFrame, index_name: str) -> pd.DataFrame:
        """Process and clean the DataFrame"""

        # Remove duplicate columns and keep only the ones we need
        columns_to_keep = ['HistoricalDate', 'OPEN', 'HIGH', 'LOW', 'CLOSE']

        # Filter to only the columns we need and that exist
        available_cols = [col for col in columns_to_keep if col in df.columns]
        df = df[available_cols].copy()

        # Rename columns for better readability
        column_mapping = {
            'HistoricalDate': 'Date',
            'OPEN': 'Open',
            'HIGH': 'High',
            'LOW': 'Low',
            'CLOSE': 'Close'
        }

        df = df.rename(columns=column_mapping)

        # Convert date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')

        # Convert numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sort by date
        if 'Date' in df.columns:
            df = df.sort_values('Date')

        # Add index name
        df['Index'] = index_name

        # Remove rows with all NaN values
        df = df.dropna(how='all')

        return df

    def get_timeframe_dates(self, timeframe: str) -> Tuple[str, str]:
        """
        Convert timeframe to start and end dates

        Args:
            timeframe: '1w', '1m', '3m', '6m', '1y', or custom format 'DD-MMM-YYYY,DD-MMM-YYYY'

        Returns:
            Tuple of (start_date, end_date) in DD-MMM-YYYY format
        """
        today = datetime.now()

        if ',' in timeframe:
            # Custom date range
            start_str, end_str = timeframe.split(',')
            return start_str.strip(), end_str.strip()

        # Predefined timeframes
        if timeframe == '1w':
            start_date = today - timedelta(weeks=1)
        elif timeframe == '1m':
            start_date = today - timedelta(days=30)
        elif timeframe == '3m':
            start_date = today - timedelta(days=90)
        elif timeframe == '6m':
            start_date = today - timedelta(days=180)
        elif timeframe == '1y':
            start_date = today - timedelta(days=365)
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}. Use '1w', '1m', '3m', '6m', '1y', or 'start_date,end_date'")

        start_str = start_date.strftime('%d-%b-%Y')
        end_str = today.strftime('%d-%b-%Y')

        return start_str, end_str

    def get_data(self, index_name, start_date, end_date, frequency="daily"):
        """
        frequency: daily, weekly, monthly, quaterly, yearly
        """
        exact_name = self.find_index_name(index_name)
        if not exact_name:
            raise ValueError(f"Index '{index_name}' not found. Use list_indices() to see available indices.")
        df = self.fetch_historical_data(exact_name, start_date, end_date)
        return self._process_data(df, frequency)

    def _freq_selection(self, df, frequency):
        if frequency == "daily":
            return df
    
        df_resampled = df.set_index('Date')
        min_date = df_resampled.index.min()
        max_date = df_resampled.index.max()
        
        if frequency == "weekly":
            result = df_resampled.resample('W').last()
        elif frequency == "monthly":
            result = df_resampled.resample('M').last()
        elif frequency == "quaterly":
            result = df_resampled.resample('QE').last()
        elif frequency == "yearly":
            result = df_resampled.resample('Y').last()
        else:
            raise ValueError(f"Invalid frequency: {frequency}. Use 'daily', 'weekly', 'monthly', 'quaterly', or 'yearly'")
        
        result = result[(result.index >= min_date) & (result.index <= max_date)]
        result = result.dropna(how='all')
        result = result.reset_index()
        return result
            
    def _process_data(self, df, frequency="daily"):
        data_dict = {}
        processed_df = self._freq_selection(df, frequency)
        for i, row in processed_df.iterrows():
            data_dict[row['Date'].strftime('%d-%b-%Y')] = row['Close']
        return data_dict

if __name__ == "__main__":
    tracker = NiftyIndicesTracker()
    print(tracker.get_data("Nifty 50", "21-Jun-2024", "21-Jun-2025", "quaterly"))
