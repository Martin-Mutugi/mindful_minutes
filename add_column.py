import psycopg2

def add_emotion_category_column():
    """
    Manually add the emotion_category column to journal_entries table
    in your Render PostgreSQL database.
    """
    try:
        # Your Render PostgreSQL connection details
        database_url = "postgresql://mindful_minutes_user:NN76jsXIcnidBqTU1G5SYnynVtRiHM6Z@dpg-d2osvc95pdvs73cvoi80-a.oregon-postgres.render.com/mindful_minutes"
        
        print("Connecting to Render PostgreSQL database...")
        
        # Connect to your Render database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # First, check if the column already exists
        print("Checking if emotion_category column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'journal_entries' 
            AND column_name = 'emotion_category'
        """)
        
        if cursor.fetchone():
            print("✓ emotion_category column already exists!")
        else:
            # Add the missing column
            print("Adding emotion_category column...")
            cursor.execute("ALTER TABLE journal_entries ADD COLUMN emotion_category VARCHAR(20);")
            conn.commit()
            print("✓ emotion_category column added successfully!")
        
        # Verify the table structure
        print("\nCurrent journal_entries table structure:")
        print("-" * 50)
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'journal_entries'
            ORDER BY ordinal_position
        """)
        
        for column in cursor.fetchall():
            print(f"{column[0]:<20} {column[1]:<15} {str(column[2] or ''):<5} {column[3]}")
        
        # Count existing journal entries
        cursor.execute("SELECT COUNT(*) FROM journal_entries")
        count = cursor.fetchone()[0]
        print(f"\nTotal journal entries in database: {count}")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Connection error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if your Render database is running")
        print("2. Verify the connection string is correct")
        print("3. Check your internet connection")
        return False
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("FIXING: Adding emotion_category column to journal_entries")
    print("Database: dpg-d2osvc95pdvs73cvoi80-a.oregon-postgres.render.com")
    print("=" * 60)
    
    success = add_emotion_category_column()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ SUCCESS: Operation completed successfully!")
        print("✓ The emotion_category column has been added")
        print("✓ Your app should now work without the column error")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ FAILED: Operation failed. Please check the error messages above.")
        print("=" * 60)