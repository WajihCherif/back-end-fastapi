import pymysql

for port in [3306, 3307]:
    for pw in ['', 'root']:
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                port=port,
                user='root',
                password=pw
            )
            print(f"SUCCESS: Port {port} with password '{pw}' connected! Server version: {conn.get_server_info()}")
            conn.close()
        except Exception as e:
            print(f"FAIL: Port {port} with password '{pw}' failed: {type(e).__name__}: {str(e)[:150]}")
