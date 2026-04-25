import os
import sys
import pymysql

def create_trigger():
    # Connect to the database directly
    # Assuming XAMPP default settings: user='root', password='', db='stock_monitoring'
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='stock_monitoring',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Successfully connected to the database.")
        
        with connection.cursor() as cursor:
            # Drop the trigger if it already exists
            cursor.execute("DROP TRIGGER IF EXISTS after_stock_update_alert;")
            
            # Create a trigger that automatically adds an alert when stock drops below 10
            trigger_sql = """
            CREATE TRIGGER after_stock_update_alert
            AFTER UPDATE ON stock
            FOR EACH ROW
            BEGIN
                IF NEW.quantity_stock < 10 AND OLD.quantity_stock >= 10 THEN
                    INSERT INTO alerts (
                        product_id, 
                        product_name, 
                        alert_type, 
                        expected_quantity, 
                        actual_quantity, 
                        difference, 
                        message, 
                        created_at
                    )
                    VALUES (
                        NEW.product_id, 
                        NEW.product_name, 
                        'Low Stock Auto-Alert', 
                        10, 
                        NEW.quantity_stock, 
                        10 - NEW.quantity_stock, 
                        CONCAT('Automatic Alert: Stock for ', NEW.product_name, ' has fallen below the minimum threshold of 10.'), 
                        NOW()
                    );
                END IF;
            END;
            """
            cursor.execute(trigger_sql)
            connection.commit()
            print("Successfully created the 'after_stock_update_alert' trigger.")
            
    except Exception as e:
        print(f"Error connecting to database or creating trigger: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    create_trigger()
