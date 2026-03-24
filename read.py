import sqlite3
import os

def read_database():
    # Check exactly where the file is
    db_path = 'workers.db'
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Error: {db_path} file not found! Please run FastAPI and start tracking first.")
        return

    try:
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("\n--- 👷 Municipal Live-Track: Database Records ---")
            
            # Select all data from the locations table
            cursor.execute("SELECT * FROM locations")
            rows = cursor.fetchall()

            if not rows:
                print("Database file exists, but no data has been saved yet.")
            else:
                # Display each row clearly
                for row in rows:
                    worker_id, lat, lon, timestamp, task = row
                    print(f"Worker ID: {worker_id:<10} | Loc: {lat:>9.5f}, {lon:>9.5f} | Time: {timestamp} | Task: {task}")
                    
    except sqlite3.OperationalError:
        print("Table 'locations' not found. Please save some data from the browser first.")
    except Exception as e:
        print(f"An error occurred while reading the DB: {e}")

if __name__ == "__main__":
    read_database()