"""
Test MongoDB connection and basic queries
"""
import sys
sys.path.append('..')

from src.connection import get_database, get_client, close_connection
from src.repositories import InventoryRepository, ServiceRepository


def test_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    
    try:
        client = get_client()
        client.admin.command('ping')
        print("✓ Connection successful!")
        
        db = get_database()
        print(f"✓ Database: {db.name}")
        print(f"✓ Collections: {db.list_collection_names()}")
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_queries():
    """Test sample queries"""
    print("\nTesting queries...")
    
    inv_repo = InventoryRepository()
    svc_repo = ServiceRepository()
    
    # Count by engine
    counts = inv_repo.count_by_engine()
    print(f"✓ Databases by engine: {counts}")
    
    # Find Oracle databases
    oracle_dbs = inv_repo.find_by_engine("ORACLE")
    print(f"✓ Oracle databases: {len(oracle_dbs)}")
    
    # Find databases with high tablespace usage
    high_usage = inv_repo.find_with_tablespace_above_threshold(90)
    print(f"✓ Databases with tablespace > 90%: {len(high_usage)}")
    
    # Get BAO for a database
    bao = svc_repo.get_bao_for_database("NZSEP")
    print(f"✓ BAO for NZSEP: {bao}")
    
    print("\nAll tests passed!")


def main():
    if test_connection():
        test_queries()
    close_connection()


if __name__ == "__main__":
    main()
