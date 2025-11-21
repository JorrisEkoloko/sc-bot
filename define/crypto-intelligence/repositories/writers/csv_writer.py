"""Generic CSV table writer with update/insert capability.

Supports both append-only tables (like MESSAGES) and update-or-insert tables
(like TOKEN_PRICES, PERFORMANCE, HISTORICAL).
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import setup_logger
from utils.key_normalizer import KeyNormalizer


class CSVTableWriter:
    """Generic CSV table writer with update/insert capability."""
    
    def __init__(self, table_name: str, columns: list[str], output_dir: str = "output", logger=None):
        """
        Initialize CSV table writer.
        
        Args:
            table_name: Name of the table (used for filename)
            columns: List of column names
            output_dir: Base output directory
            logger: Optional logger instance
        """
        self.table_name = table_name
        self.columns = columns
        self.output_dir = Path(output_dir)
        self.logger = logger or setup_logger(f'CSVTableWriter[{table_name}]')
        self.current_file = None
        self.current_date = None
        
        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"CSV table writer initialized for '{table_name}' ({len(columns)} columns)")
    
    def append(self, row: list):
        """
        Append row to table (for append-only tables like MESSAGES).
        
        Args:
            row: List of values matching column order
        """
        try:
            self._ensure_file()
            with open(self.current_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            self.logger.debug(f"Appended row to {self.table_name}")
        except Exception as e:
            self.logger.error(f"Failed to append row to {self.table_name}: {e}")
            # Don't re-raise - allow system to continue with other operations
    
    def update_or_insert(self, key: str, row: list):
        """
        Update existing row or insert new row (for tables like TOKEN_PRICES, PERFORMANCE).
        
        The key is matched against the first column (assumed to be the primary key).
        
        Args:
            key: Primary key value (first column)
            row: List of values matching column order
        """
        try:
            self._ensure_file()
            
            # Read all rows
            rows = []
            if self.current_file.exists():
                with open(self.current_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            
            # If file is empty or only has header, add header
            if not rows:
                rows = [self.columns]
            
            # Normalize key for comparison using KeyNormalizer
            normalized_key = KeyNormalizer.normalize_key_by_column(key, 0, self.table_name)
            
            # Find row with matching key (first column)
            updated = False
            for i, existing_row in enumerate(rows[1:], start=1):  # Skip header
                if existing_row:
                    # Normalize existing key for comparison using KeyNormalizer
                    existing_key = KeyNormalizer.normalize_key_by_column(existing_row[0], 0, self.table_name)
                    
                    if existing_key == normalized_key:
                        rows[i] = row
                        updated = True
                        self.logger.debug(f"Updated existing row in {self.table_name} (key: {normalized_key[:10]}...)")
                        break
            
            # If not found, append
            if not updated:
                rows.append(row)
                self.logger.debug(f"Inserted new row in {self.table_name} (key: {normalized_key[:10]}...)")
            
            # Write all rows back
            with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert row in {self.table_name}: {e}")
            # Don't re-raise - allow system to continue with other operations
    
    def update_or_insert_composite(self, key_values: list, row: list, key_column_indices: list = None):
        """
        Update existing row or insert new row using composite key.
        
        The key_values are matched against specified columns or the first N columns.
        
        Args:
            key_values: List of values for composite key (e.g., [address, symbol, message_id])
            row: List of values matching column order
            key_column_indices: Optional list of column indices to use as key (e.g., [0, 2, 3])
                               If None, uses first N columns sequentially
        """
        try:
            self._ensure_file()
            
            # Read all rows
            rows = []
            if self.current_file.exists():
                with open(self.current_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            
            # If file is empty or only has header, add header
            if not rows:
                rows = [self.columns]
            
            # Determine which columns to use for key matching
            if key_column_indices is None:
                # Default: use first N columns sequentially
                key_column_indices = list(range(len(key_values)))
            
            # Normalize key values for comparison using KeyNormalizer
            normalized_key_values = KeyNormalizer.normalize_composite_key(
                key_values, key_column_indices, self.table_name
            )
            
            # Find row with matching composite key
            updated = False
            for i, existing_row in enumerate(rows[1:], start=1):  # Skip header
                if existing_row and len(existing_row) > max(key_column_indices):
                    # Extract and normalize key values from existing row using KeyNormalizer
                    existing_key_raw = [existing_row[col_idx] for col_idx in key_column_indices]
                    existing_key_values = KeyNormalizer.normalize_composite_key(
                        existing_key_raw, key_column_indices, self.table_name
                    )
                    
                    # Check if all key columns match
                    if existing_key_values == normalized_key_values:
                        rows[i] = row
                        updated = True
                        key_str = '|'.join(str(k)[:10] for k in key_values)
                        self.logger.debug(f"Updated existing row in {self.table_name} (key: {key_str}...)")
                        break
            
            # If not found, append
            if not updated:
                rows.append(row)
                key_str = '|'.join(str(k)[:10] for k in key_values)
                self.logger.debug(f"Inserted new row in {self.table_name} (key: {key_str}...)")
            
            # Write all rows back
            with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert row with composite key in {self.table_name}: {e}")
            # Don't re-raise - allow system to continue with other operations
    
    def _ensure_file(self):
        """Ensure CSV file exists with header."""
        today = datetime.now().date()
        
        # Check if we need to rotate file
        if self.current_date != today:
            self._rotate_file(today)
    
    def _rotate_file(self, date):
        """
        Rotate to new file for the given date.
        
        Args:
            date: Date for the new file
        """
        # Create date-specific directory
        date_dir = self.output_dir / date.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Set new file path
        self.current_file = date_dir / f"{self.table_name}.csv"
        self.current_date = date
        
        # Create file with header if it doesn't exist
        if not self.current_file.exists():
            try:
                with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.columns)
                
                self.logger.info(f"Created new CSV file: {self.current_file}")
            except Exception as e:
                self.logger.error(f"Failed to create CSV file: {e}")
                raise
    
    def get_current_file(self) -> Optional[Path]:
        """
        Get the current CSV file path.
        
        Returns:
            Path to current CSV file or None
        """
        self._ensure_file()
        return self.current_file
    
    def read_all_rows(self) -> list[list]:
        """
        Read all rows from current file (including header).
        
        Returns:
            List of rows (each row is a list of values)
        """
        self._ensure_file()
        
        try:
            with open(self.current_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                return list(reader)
        except Exception as e:
            self.logger.error(f"Failed to read rows from {self.table_name}: {e}")
            return []
    
    def count_rows(self) -> int:
        """
        Count rows in current file (excluding header).
        
        Returns:
            Number of data rows
        """
        rows = self.read_all_rows()
        return max(0, len(rows) - 1)  # Subtract header row
    
    def clear(self):
        """
        Clear all data rows from current file (keep header).
        """
        try:
            self._ensure_file()
            with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
            self.logger.info(f"Cleared all data from {self.table_name}")
        except Exception as e:
            self.logger.error(f"Failed to clear {self.table_name}: {e}")

