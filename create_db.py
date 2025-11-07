import duckdb
import pandas as pd
import json
import os

DATABASE_FILE = "uber_trips.db"
KNOWLEDGE_BASE_FILE = "knowledge_base.json"

def create_and_populate_db():
    """Creates a sample DuckDB database mirroring Uber's domain."""
    print(f"Creating and populating database: {DATABASE_FILE}...")
    
    # Ensure the database file is clean before starting
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        
    con = duckdb.connect(database=DATABASE_FILE)
    
    # 1. trips table (Mobility Workspace)
    trips_data = {
        'trip_id': range(1, 11),
        'driver_id': [101, 102, 101, 103, 102, 101, 104, 105, 103, 105],
        'city': ['Seattle', 'SF', 'Seattle', 'NY', 'SF', 'Seattle', 'NY', 'SF', 'NY', 'Seattle'],
        'distance_miles': [5.2, 12.1, 3.5, 8.9, 1.1, 7.8, 4.0, 15.0, 2.5, 6.7],
        'fare_usd': [15.50, 32.00, 10.25, 20.00, 7.50, 18.99, 11.00, 45.00, 9.99, 16.00],
        'trip_status': ['completed', 'completed', 'completed', 'cancelled', 'completed', 'completed', 'completed', 'completed', 'completed', 'completed'],
        'trip_date': pd.to_datetime(['2025-10-23', '2025-10-23', '2025-10-24', '2025-10-24', '2025-10-23', '2025-10-24', '2025-10-23', '2025-10-24', '2025-10-24', '2025-10-23'])
    }
    
    # CONVERT DICT TO PANDAS DATAFRAME
    trips_df = pd.DataFrame(trips_data)
    
    # Create and populate the table from the DataFrame
    con.execute("CREATE TABLE trips AS SELECT * FROM trips_df") 
    
    # 2. drivers table (Core Services/HR Workspace)
    drivers_data = {
        'driver_id': [101, 102, 103, 104, 105],
        'name': ['Alice', 'Bob', 'Charlie', 'Dana', 'Eve'],
        'license_status': ['active', 'active', 'suspended', 'active', 'active'],
        'vehicle_make': ['Toyota', 'Honda', 'Ford', 'Tesla', 'Nissan'],
        'hire_date': pd.to_datetime(['2024-01-15', '2023-05-20', '2025-01-01', '2024-11-11', '2023-10-10']),
        'annual_bonus_target': [500, 600, 300, 800, 500],
        'current_rating': [4.8, 4.5, 3.9, 4.9, 4.6],
        'long_term_retention_score': [0.95, 0.88, 0.45, 0.99, 0.90] # Pruning target
    }
    
    # CONVERT DICT TO PANDAS DATAFRAME
    drivers_df = pd.DataFrame(drivers_data)
    
    # Create and populate the table from the DataFrame
    con.execute("CREATE TABLE drivers AS SELECT * FROM drivers_df")

    con.close()
    print("Database created successfully.")

def create_knowledge_base():
    """Creates a simplified RAG knowledge base (JSON for demo) for the agents."""
    kb = {
        "Mobility": {
            "description": "Contains data related to rides, vehicles, and real-time trip details.",
            "tables": {
                "trips": {
                    "schema": "trip_id (INT), driver_id (INT), city (VARCHAR), distance_miles (FLOAT), fare_usd (FLOAT), trip_status (VARCHAR), trip_date (DATE)",
                    "rules": "The column `trip_status` must be 'completed' to count a successful trip. Always filter by `trip_date` when a time frame is provided.",
                    "sample_query": "SELECT count(trip_id) FROM trips WHERE trip_date = '2025-10-24' AND trip_status = 'completed';"
                }
            }
        },
        "Core Services": {
            "description": "Contains HR, payroll, and static user/driver data.",
            "tables": {
                "drivers": {
                    "schema": "driver_id (INT), name (VARCHAR), license_status (VARCHAR), vehicle_make (VARCHAR), hire_date (DATE), annual_bonus_target (INT), current_rating (FLOAT), long_term_retention_score (FLOAT)",
                    "rules": "To check for an active driver, filter on `license_status` = 'active'. The `long_term_retention_score` column is rarely needed.",
                    "sample_query": "SELECT name, current_rating FROM drivers WHERE license_status = 'active';"
                }
            }
        }
    }
    
    with open(KNOWLEDGE_BASE_FILE, 'w') as f:
        json.dump(kb, f, indent=4)
    print(f"Knowledge Base created: {KNOWLEDGE_BASE_FILE}")

if __name__ == "__main__":
    create_and_populate_db()
    create_knowledge_base()