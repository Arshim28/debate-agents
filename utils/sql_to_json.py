import sqlite3
import json
import os

def convert_sql_to_json():
    """
    Convert SQLite database to JSON format with company ID as keys
    and all other fields as dictionary values
    """
    # Path to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trendlyne.db")
    
    # Path for output JSON file
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
    output_path = os.path.join(config_dir, "trendlyne_db.json")
    
    # Ensure config directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    try:
        # Connect to the database
        sql_conn = sqlite3.connect(db_path, timeout=20.0)
        cursor = sql_conn.cursor()
        
        # Get table schema first
        cursor.execute("PRAGMA table_info(companies)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Found columns: {column_names}")
        
        # Get all data from companies table
        cursor.execute("SELECT * FROM companies")
        rows = cursor.fetchall()
        sql_conn.close()
        
        # Convert to JSON format
        json_data = {}
        
        for row in rows:
            # Create a dictionary for each row
            row_dict = {}
            company_id = None
            
            for i, value in enumerate(row):
                column_name = column_names[i]
                
                # Use trendlyne_stock_id as the key
                if column_name == 'trendlyne_stock_id':
                    company_id = str(value) if value is not None else str(i)
                else:
                    row_dict[column_name] = value
            
            # Add to JSON data with company ID as key
            if company_id:
                json_data[company_id] = row_dict
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted {len(json_data)} records to JSON")
        print(f"Output file: {output_path}")
        
        # Print sample data
        if json_data:
            sample_key = list(json_data.keys())[0]
            print(f"\nSample record (ID: {sample_key}):")
            print(json.dumps(json_data[sample_key], indent=2))
        
        return output_path
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    convert_sql_to_json()
