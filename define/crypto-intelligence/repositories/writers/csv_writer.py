"""Generic CSV table writer with update/insert capability.

Supports both append-only tables (like MESSAGES) and update-or-insert tables
(like TOKEN_PRICES, PERFORMANCE, HISTORICAL).
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import setup_logger


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
        self._ensure_file()
        
        try:
            with open(self.current_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            self.logger.debug(f"Appended row to {self.table_name}")
        except Exception as e:
            self.logger.error(f"Failed to append row to {self.table_name}: {e}")
            raise
    
    def update_or_insert(self, key: str, row: list):
        """
        Update existing row or insert new row (for tables like TOKEN_PRICES, PERFORMANCE).
        
        The key is matched against the first column (assumed to be the primary key).
        
        Args:
            key: Primary key value (first column)
            row: List of values matching column order
        """
        self._ensure_file()
        
        try:
            # Read all rows
            rows = []
            if self.current_file.exists():
                with open(self.current_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            
            # If file is empty or only has header, add header
            if not rows:
                rows = [self.columns]
            
            # Find row with matching key (first column)
            updated = False
            for i, existing_row in enumerate(rows[1:], start=1):  # Skip header
                if existing_row and existing_row[0] == key:
                    rows[i] = row
                    updated = True
                    self.logger.debug(f"Updated existing row in {self.table_name} (key: {key[:10]}...)")
                    break
            
            # If not found, append
            if not updated:
                rows.append(row)
                self.logger.debug(f"Inserted new row in {self.table_name} (key: {key[:10]}...)")
            
            # Write all rows back
            with open(self.current_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
                
        except Exception as e:
            self.logger.error(f"Failed to update/insert row in {self.table_name}: {e}")
            raise
    
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

