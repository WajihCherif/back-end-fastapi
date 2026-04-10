import pymysql

# Test connection with no password
print("Testing MySQL connection...")
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',  # Empty for XAMPP
        database='mysql'
    )
    print("✅ Successfully connected to MySQL!")
    print(f"MySQL Version: {connection.get_server_info()}")
    connection.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    
    # Try alternative
    print("\nTrying alternative connection...")
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='mysql'
        )
        print("✅ Connected via 127.0.0.1!")
        connection.close()
    except Exception as e2:
        print(f"❌ Still failing: {e2}")