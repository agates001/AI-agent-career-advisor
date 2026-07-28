import sqlite3
from typing import List, Dict, Any

## NOTES:
## Connect to a local file (creates it if it doesn't exist)
## This is an open pipeline to the database file.
## We will use this connection (conn) to save changes
## such as via commit or to close the connection - close().
## Here conn is an instance of the sqlites3.Connection class. 
## It manages system level file desc or mem mapping, etc/
## The cursor is a control structure that we will use to interact with the database. 
## The cursor here is an instance of the sqlite3.Cursor class. It controls 
## statement exectution. 
## whatever you name the connection - called conn here
## you will need to use that variable name for the cursor().
## !! cursor and conn are variable names. They are common in industry but can be changed if you wish.

######################################
# DATABASE SYSTEM SETUP
######################################
import sqlite3
from typing import List, Dict, Any

# 1. DATABASE SYSTEM SETUP
def init_student_db():
    conn = sqlite3.connect("MySmallDatabase.db")
    cursor = conn.cursor()
    
    # Enable foreign key support in SQLite (disabled by default)
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Master student table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        major TEXT NOT NULL,
        gpa REAL NOT NULL
    )
    """)
    
    # Relational table to track classes taken (Many-to-Many or One-to-Many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes_taken (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        class_name TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)
    
    # Mock data payloads
    mock_students = [
        (101, 'Alice', 'Smith', 'alice.smith@university.edu', 'Computer Science', 3.85),
        (102, 'Bob', 'Jones', 'bob.jones@university.edu', 'Data Science', 3.42),
        (103, 'Charlie', 'Brown', 'charlie.b@university.edu', 'Computer Science', 2.90)
    ]
    
    mock_classes = [
        (101, 'CS101 - Intro to Programming'),
        (101, 'MATH201 - Linear Algebra'),
        (102, 'DS101 - Intro to Data Science'),
        (102, 'STAT301 - Probability'),
        (103, 'CS101 - Intro to Programming')
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO students VALUES (?, ?, ?, ?, ?, ?)", mock_students)
    cursor.executemany("INSERT OR IGNORE INTO classes_taken (student_id, class_name) VALUES (?, ?)", mock_classes)
    
    conn.commit()
    conn.close()
    print("Database 'MySmallDatabase.db' initialized successfully.")

# 2. THE RAG INTERFACE FOR THE AI WORKFLOW
class StudentSQLRAGTool:
    """A safe Text-to-SQL tool executing queries against MySmallDatabase.db."""
    
    def __init__(self, db_path: str = "MySmallDatabase.db"):
        self.db_path = db_path

    def get_schema(self) -> str:
        """
        Extracts DDL statements for the students and classes_taken tables.
        Provides the schema context required by LLMs to construct valid queries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('students', 'classes_taken');")
        schemas = [row[0] for row in cursor.fetchall() if row[0]]
        
        conn.close()
        return "\n\n".join(schemas)

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Executes raw SELECT strings against the database.
        Returns rows as native Python dictionaries.
        """
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
            return [{"error": "Security violation: Write operations are restricted."}]

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Maps column headers to row values
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            conn.close()
            return result
            
        except sqlite3.Error as e:
            return [{"error": f"SQL Syntax Error: {str(e)}"}]

# Local Execution Verification
if __name__ == "__main__":
    init_student_db()
    db_tool = StudentSQLRAGTool()
    
    print("\n[SCHEMA RETRIEVAL OUTPUT]")
    print(db_tool.get_schema())
    
    print("\n[SQL EXECUTION OUTPUT]")
    # Relational JOIN to fetch students taking CS101
    sample_query = """
    SELECT s.id, s.first_name, s.last_name, c.class_name 
    FROM students s
    JOIN classes_taken c ON s.id = c.student_id
    WHERE c.class_name LIKE '%CS101%';
    """
    print(db_tool.execute_query(sample_query))