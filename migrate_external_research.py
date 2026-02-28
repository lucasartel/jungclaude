import logging
from jung_core import HybridDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db = HybridDatabaseManager()
    cursor = db.conn.cursor()
    
    logger.info("Criando tabela external_research...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            
            topic TEXT NOT NULL,
            source_url TEXT,
            raw_excerpt TEXT,
            synthesized_insight TEXT,
            
            status TEXT DEFAULT 'active', -- 'active', 'archived'
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    db.conn.commit()
    logger.info("Migração finalizada.")
    db.close()

if __name__ == "__main__":
    migrate()
