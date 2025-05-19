import sqlite3
from db_manager import DBManager

def update_schema():
    db_manager = DBManager()
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()
    
    # Check if department column exists
    cursor.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "department" not in columns:
        print("Adding department column to conversations table...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN department TEXT")
        conn.commit()
        print("Department column added successfully!")
    
    # Update missing departments
    updated = db_manager.update_missing_departments()
    print(f"Updated {updated} conversations with department information")
    
    conn.close()

if __name__ == "__main__":
    update_schema()