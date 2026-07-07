import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'importador.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript('''
        CREATE TABLE IF NOT EXISTS layouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo_arquivo TEXT NOT NULL DEFAULT 'xlsx',
            separador_csv TEXT DEFAULT ',',
            linha_inicio INTEGER NOT NULL DEFAULT 2,
            tabela_oracle TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campos_layout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_id INTEGER NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
            campo_oracle TEXT NOT NULL,
            tipo_mapeamento TEXT NOT NULL,
            coluna_planilha TEXT,
            valor_fixo TEXT
        );

        CREATE TABLE IF NOT EXISTS importacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_id INTEGER REFERENCES layouts(id),
            nome_layout TEXT,
            nome_arquivo TEXT,
            total_linhas INTEGER DEFAULT 0,
            linhas_importadas INTEGER DEFAULT 0,
            linhas_erro INTEGER DEFAULT 0,
            status TEXT DEFAULT "pendente",
            log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    db.commit()

    # Migração: recriar campos_layout sem CHECK constraint se o valor 'sequence' for rejeitado
    try:
        db.execute("INSERT INTO campos_layout (layout_id, campo_oracle, tipo_mapeamento) VALUES (-1, '__migtest__', 'sequence')")
        db.execute("DELETE FROM campos_layout WHERE layout_id = -1")
        db.commit()
    except Exception:
        db.rollback()
        db.execute("ALTER TABLE campos_layout RENAME TO campos_layout_bak")
        db.execute("""CREATE TABLE campos_layout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_id INTEGER NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
            campo_oracle TEXT NOT NULL,
            tipo_mapeamento TEXT NOT NULL,
            coluna_planilha TEXT,
            valor_fixo TEXT
        )""")
        db.execute("INSERT INTO campos_layout SELECT * FROM campos_layout_bak")
        db.execute("DROP TABLE campos_layout_bak")
        db.commit()

    db.close()
