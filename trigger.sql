DELIMITER //
DROP TRIGGER IF EXISTS after_stock_update_alert //

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
//
DELIMITER ;
