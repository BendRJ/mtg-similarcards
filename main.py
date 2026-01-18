from database.db import test_connection, get_cursor


def main():
    print("Hello from mtg-similarcards!")
    print("\nTesting database connection...")
    
    if test_connection():
        print("✓ Database connection successful!")
        
        # Example: Query the sets table
        print("\nQuerying sets table...")
        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sets")
                result = cur.fetchone()
                if result:
                    count = result[0]
                    print(f"✓ Sets table exists with {count} records")
                else:
                    print("✓ Sets table exists but query returned no results")
        except Exception as e:
            print(f"✗ Error querying sets table: {e}")
    else:
        print("✗ Database connection failed!")
        print("Make sure the database is running: docker compose up -d")


if __name__ == "__main__":
    main()
