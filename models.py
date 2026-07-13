import sqlite3
import os
import sys
from flask import g

# Quando frozen (PyInstaller one-file), __file__ aponta para o diretório
# temporário de extração que muda a cada execução. sys.executable aponta
# para o EXE real — que é onde o banco deve persistir.
if getattr(sys, 'frozen', False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_BASE, 'importador.db')

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

    # Migração: recriar campos_layout sem CHECK constraint se necessário
    schema_row = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='campos_layout'"
    ).fetchone()
    if schema_row and 'CHECK' in schema_row[0].upper():
        db.execute("DROP TABLE IF EXISTS campos_layout_bak")
        db.execute("ALTER TABLE campos_layout RENAME TO campos_layout_bak")
        db.execute("""CREATE TABLE campos_layout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_id INTEGER NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
            campo_oracle TEXT NOT NULL,
            tipo_mapeamento TEXT NOT NULL,
            coluna_planilha TEXT,
            valor_fixo TEXT,
            mascara_data TEXT
        )""")
        cols_bak = [r[1] for r in db.execute("PRAGMA table_info(campos_layout_bak)").fetchall()]
        cols_new = ['id', 'layout_id', 'campo_oracle', 'tipo_mapeamento',
                    'coluna_planilha', 'valor_fixo', 'mascara_data']
        src_cols = ', '.join(c if c in cols_bak else 'NULL' for c in cols_new)
        db.execute(f"INSERT INTO campos_layout SELECT {src_cols} FROM campos_layout_bak")
        db.execute("DROP TABLE campos_layout_bak")
        db.commit()

    # Migração: adicionar coluna mascara_data se não existir
    try:
        db.execute("ALTER TABLE campos_layout ADD COLUMN mascara_data TEXT")
        db.commit()
    except Exception:
        pass

    # Migração: adicionar coluna substr_regra se não existir
    try:
        db.execute("ALTER TABLE campos_layout ADD COLUMN substr_regra TEXT")
        db.commit()
    except Exception:
        pass

    # Migração: regex de extração e valor padrão
    try:
        db.execute("ALTER TABLE campos_layout ADD COLUMN regex_extrair TEXT")
        db.commit()
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE campos_layout ADD COLUMN valor_padrao TEXT")
        db.commit()
    except Exception:
        pass

    # Migração: de-para de valores por campo (JSON)
    try:
        db.execute("ALTER TABLE campos_layout ADD COLUMN depara_json TEXT")
        db.commit()
    except Exception:
        pass

    # Limpar tabela de backup residual de migrações anteriores
    db.execute("DROP TABLE IF EXISTS campos_layout_bak")
    db.commit()

    db.close()
