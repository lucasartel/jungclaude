import os
import logging
os.environ["OPENROUTER_API_KEY"] = ""  
logging.basicConfig(level=logging.INFO)
from jung_core import HybridDatabaseManager, JungianEngine, Config
Config.INTERNAL_MODEL = "claude-3-haiku-20240307"

db = HybridDatabaseManager()
engine = JungianEngine(db)

print('\n\n--- Admin Test With Append ---')
result_admin = engine.process_message('367f9e509e396d51', 'O que você achou dos meus sentimentos?')
import sys
sys.stdout.buffer.write(result_admin['response'].encode('utf-8'))

db.close()
