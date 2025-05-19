import sqlite3
import json

def add_department_column():
    """Add department column to conversations table"""
    conn = sqlite3.connect("data/conversation_database.db")
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "department" not in columns:
            print("Adding department column to conversations table...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN department TEXT")
            print("Column added successfully!")
        else:
            print("Column 'department' already exists.")
        
        # Update existing rows with department information
        with open("data/employee_database.json", "r") as f:
            employee_data = json.load(f)
        
        cursor.execute("SELECT id, employee_id FROM conversations")
        conversations = cursor.fetchall()
        
        for conv_id, emp_id in conversations:
            department = employee_data.get(emp_id, {}).get("department", "Unknown")
            cursor.execute(
                "UPDATE conversations SET department = ? WHERE id = ?", 
                (department, conv_id)
            )
        
        conn.commit()
        print("Department information updated successfully!")
    
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_department_column()
