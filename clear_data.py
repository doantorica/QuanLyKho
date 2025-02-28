import mysql.connector
from database import DB_CONFIG, InventoryManager


def clear_cache():
    conn = mysql.connector.connect(**DB_CONFIG)
    inventory_manager = InventoryManager(conn)

    # Xóa toàn bộ cache
    inventory_manager.items_cache = None
    inventory_manager.sales_cache = None
    inventory_manager.import_cache = None
    inventory_manager.machines_cache = None
    inventory_manager.photocopy_sales_cache = None
    inventory_manager.rental_cache = None
    inventory_manager.maintenance_cache = None
    inventory_manager.cache_changed = {key: True for key in inventory_manager.cache_changed}

    print("Đã làm mới toàn bộ cache!")
    conn.close()


if __name__ == "__main__":
    clear_cache()