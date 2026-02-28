import logging
import traceback
from jung_core import HybridDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db = HybridDatabaseManager()
    cursor = db.conn.cursor()
    
    try:
        logger.info("Adding image_prompt column to agent_dreams...")
        cursor.execute("ALTER TABLE agent_dreams ADD COLUMN image_prompt TEXT;")
    except Exception as e:
        logger.warning(f"Column image_prompt might already exist: {e}")

    try:
        logger.info("Adding image_url column to agent_dreams...")
        cursor.execute("ALTER TABLE agent_dreams ADD COLUMN image_url TEXT;")
    except Exception as e:
        logger.warning(f"Column image_url might already exist: {e}")

    db.conn.commit()
    logger.info("Migration finished.")
    db.close()

if __name__ == "__main__":
    migrate()
