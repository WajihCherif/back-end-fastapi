import pymysql

configs = [
    {"port": 3306, "password": "root", "name": "MySQL on 3306 (pw: root)"},
    {"port": 3307, "password": "", "name": "MySQL on 3307 (pw: empty)"}
]

for config in configs:
    print(f"\nChecking {config['name']}...")
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=config['port'],
            user='root',
            password=config['password']
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [row[0] for row in cursor.fetchall()]
        print(f"Databases: {dbs}")
        
        if "stock_monitoring" in dbs:
            print("Found 'stock_monitoring' database!")
            conn.select_db("stock_monitoring")
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tables: {tables}")
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
                count = cursor.fetchone()[0]
                print(f"  Table `{t}` has {count} rows")
        else:
            print("'stock_monitoring' database does NOT exist on this server.")
        conn.close()
    except Exception as e:
        print(f"Error checking {config['name']}: {e}")
