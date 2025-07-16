"""
Database module for MINT package.
Provides SQLiteBuilder class for creating SQLite databases from metadata.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class SQLiteBuilder:
    """
    A class to build SQLite databases from table metadata JSON files.
    
    This class parses table structure information and creates corresponding
    SQLite databases that can be used for SQL query execution and testing.
    """
    
    def __init__(self, output_dir: str = "sqlite_dbs"):
        """
        Initialize SQLiteBuilder.
        
        Args:
            output_dir (str): Directory to store created SQLite databases
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the builder."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize table and column names for SQLite.
        
        Args:
            name (str): Original name
            
        Returns:
            str: Sanitized name safe for SQLite
        """
        # Replace problematic characters
        name = name.replace(" ", "_").replace("-", "_").replace(".", "_")
        # Remove other special characters except underscore
        sanitized = "".join(c for c in name if c.isalnum() or c == "_")
        # Ensure name doesn't start with number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"col_{sanitized}"
        return sanitized or "unknown_column"
    
    def _get_sqlite_type(self, col_type: str) -> str:
        """
        Convert table metadata type to SQLite type.
        
        Args:
            col_type (str): Original column type
            
        Returns:
            str: SQLite compatible type
        """
        col_type = col_type.lower()
        
        if col_type in ['text', 'varchar', 'char', 'string']:
            return 'TEXT'
        elif col_type in ['int', 'integer', 'bigint', 'smallint']:
            return 'INTEGER'
        elif col_type in ['real', 'float', 'double', 'decimal', 'numeric']:
            return 'REAL'
        elif col_type in ['date', 'datetime', 'timestamp']:
            return 'TEXT'  # Store as text in SQLite
        else:
            return 'TEXT'  # Default fallback
    
    def _detect_duplicates(self, columns: List[Dict]) -> List[str]:
        """
        Detect duplicate column names.
        
        Args:
            columns (List[Dict]): List of column definitions
            
        Returns:
            List[str]: List of duplicate column names
        """
        seen = set()
        duplicates = []
        
        for col in columns:
            sanitized_name = self._sanitize_name(col['column_name'])
            if sanitized_name in seen:
                duplicates.append(col['column_name'])
            seen.add(sanitized_name)
            
        return duplicates
    
    def _create_table_schema(self, table_info: Dict) -> Tuple[str, List[str]]:
        """
        Create SQL schema for a table.
        
        Args:
            table_info (Dict): Table metadata
            
        Returns:
            Tuple[str, List[str]]: SQL CREATE statement and list of warnings
        """
        table_name = self._sanitize_name(table_info['table_name'])
        columns = table_info['column_names']
        types = table_info['column_types']
        
        warnings = []
        
        # Check for duplicates
        duplicates = self._detect_duplicates([
            {'column_name': col} for col in columns
        ])
        if duplicates:
            warnings.append(f"Duplicate columns detected: {duplicates}")
            return "", warnings
        
        # Build column definitions
        column_defs = []
        for i, (col_name, col_type) in enumerate(zip(columns, types)):
            sanitized_name = self._sanitize_name(col_name)
            sqlite_type = self._get_sqlite_type(col_type)
            
            # Add PRIMARY KEY to first column if it looks like an ID
            if i == 0 and ('id' in col_name.lower() or sanitized_name.lower().endswith('_id')):
                column_defs.append(f'"{sanitized_name}" {sqlite_type} PRIMARY KEY')
            else:
                column_defs.append(f'"{sanitized_name}" {sqlite_type}')
        
        # Create table statement
        column_defs_str = ',\n            '.join(column_defs)
        create_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {column_defs_str}
        );
        '''
        
        return create_sql.strip(), warnings
    
    def build_database(self, tables_json_path: str, db_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Build SQLite database from tables.json file.
        
        Args:
            tables_json_path (str): Path to tables.json file
            db_name (Optional[str]): Custom database name. If None, derives from file path
            
        Returns:
            Dict[str, Any]: Build result with statistics and warnings
        """
        try:
            # Load tables metadata
            with open(tables_json_path, 'r', encoding='utf-8') as f:
                tables_data = json.load(f)
            
            # Determine database name
            if db_name is None:
                # Extract from path: dataset/ViText2SQL/syllable-level/tables.json -> syllable-level
                path_parts = Path(tables_json_path).parts
                if len(path_parts) >= 2:
                    db_name = f"{path_parts[-2]}_vitext2sql"
                else:
                    db_name = "vitext2sql"
            
            db_path = self.output_dir / f"{db_name}.db"
            
            # Create database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            results = {
                'database_path': str(db_path),
                'total_tables': len(tables_data),
                'created_tables': 0,
                'failed_tables': 0,
                'warnings': [],
                'failed_table_names': []
            }
            
            # Create each table
            for table_info in tables_data:
                try:
                    create_sql, warnings = self._create_table_schema(table_info)
                    
                    if warnings:
                        results['warnings'].extend(warnings)
                        results['failed_tables'] += 1
                        results['failed_table_names'].append(table_info['table_name'])
                        continue
                    
                    cursor.execute(create_sql)
                    results['created_tables'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to create table {table_info.get('table_name', 'unknown')}: {e}")
                    results['failed_tables'] += 1
                    results['failed_table_names'].append(table_info.get('table_name', 'unknown'))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Database created: {db_path}")
            self.logger.info(f"Tables created: {results['created_tables']}/{results['total_tables']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Failed to build database: {e}"
            self.logger.error(error_msg)
            return {
                'error': error_msg,
                'database_path': None,
                'total_tables': 0,
                'created_tables': 0,
                'failed_tables': 0,
                'warnings': [],
                'failed_table_names': []
            }
    
    def build_all_databases(self, dataset_root: str = "dataset/ViText2SQL") -> Dict[str, Dict[str, Any]]:
        """
        Build databases for all versions in the dataset.
        
        Args:
            dataset_root (str): Root directory of the dataset
            
        Returns:
            Dict[str, Dict[str, Any]]: Results for each version
        """
        results = {}
        dataset_path = Path(dataset_root)
        
        # Find all tables.json files
        for version_dir in dataset_path.iterdir():
            if version_dir.is_dir():
                tables_file = version_dir / "tables.json"
                if tables_file.exists():
                    self.logger.info(f"Building database for {version_dir.name}")
                    results[version_dir.name] = self.build_database(
                        str(tables_file), 
                        version_dir.name
                    )
        
        return results
    
    def get_database_info(self, db_path: str) -> Dict[str, Any]:
        """
        Get information about created database.
        
        Args:
            db_path (str): Path to SQLite database
            
        Returns:
            Dict[str, Any]: Database information
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            info = {
                'database_path': db_path,
                'table_count': len(tables),
                'tables': {}
            }
            
            # Get info for each table
            for table in tables:
                cursor.execute(f'PRAGMA table_info("{table}");')
                columns = cursor.fetchall()
                
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                row_count = cursor.fetchone()[0]
                
                info['tables'][table] = {
                    'columns': [col[1] for col in columns],  # Column names
                    'column_types': [col[2] for col in columns],  # Column types
                    'row_count': row_count
                }
            
            conn.close()
            return info
            
        except Exception as e:
            return {
                'error': f"Failed to get database info: {e}",
                'database_path': db_path,
                'table_count': 0,
                'tables': {}
            } 