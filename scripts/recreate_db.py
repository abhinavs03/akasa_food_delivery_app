"""
Script to recreate the database with updated schema.
WARNING: This will delete all existing data!
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, create_db_and_tables
from app.models import User, Category, Item, CartItem, Order, OrderItem, Payment

def main():
    # Delete existing database
    db_path = "data.db"
    if os.path.exists(db_path):
        print(f"Deleting existing database: {db_path}")
        os.remove(db_path)
    
    # Recreate database with new schema
    print("Creating new database with updated schema...")
    create_db_and_tables()
    
    print("Database recreated successfully!")
    print("Note: You'll need to run seed.py again to populate items.")

if __name__ == "__main__":
    main()

