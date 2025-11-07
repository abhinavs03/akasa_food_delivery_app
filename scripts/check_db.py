import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, text
from app.database import engine

with Session(engine) as session:
    result = session.exec(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result]
    print("Existing tables:", tables)
    
    if 'payment' not in tables:
        print("\n❌ Payment table is MISSING!")
    else:
        print("\n✅ Payment table exists")
    
    # Check if order table has payment_status column (use quotes for reserved keyword)
    try:
        result = session.exec(text('PRAGMA table_info("order")'))
        columns = [row[1] for row in result]
        print("\nOrder table columns:", columns)
        if 'payment_status' in columns:
            print("✅ Order table has payment_status column")
        else:
            print("❌ Order table is MISSING payment_status column!")
            print("\nTo fix: Delete data.db and restart the server")
    except Exception as e:
        print(f"Error checking order table: {e}")
