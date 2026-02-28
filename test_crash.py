import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
from jung_core import HybridDatabaseManager, JungianEngine

os.environ["ADMIN_USER_ID"] = "1228514589"
db = HybridDatabaseManager()
engine = JungianEngine(db)

try:
    print('\n\n--- User Test ---')
    # Using '_generate_response' directly to bypass 'process_message' try-except
    res = engine._generate_response('userXYZ', 'Oi, teste.', 'contexto', [])
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()

db.close()
