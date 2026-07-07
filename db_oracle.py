import oracledb
import json
import os

CONFIG_PATH = r'C:\Viasoft\Client\PlugIns\pluggy_config.json'

_thick_initialized = False

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_connection():
    global _thick_initialized
    config = load_config()
    oracle_cfg = config.get('oracle', {})

    usuario = oracle_cfg.get('usuario', '')
    senha = oracle_cfg.get('senha', '')
    modo = oracle_cfg.get('modo_conexao', 'DIRETO')

    if modo == 'TNS':
        tns_cfg = oracle_cfg.get('tns', {})
        client_bin = tns_cfg.get('oracle_client_bin', '')
        if client_bin and not _thick_initialized:
            oracledb.init_oracle_client(lib_dir=client_bin)
            _thick_initialized = True
        tnsnames_path = tns_cfg.get('tnsnames_path', '')
        if tnsnames_path:
            os.environ['TNS_ADMIN'] = tnsnames_path
        dsn = tns_cfg.get('alias', '')
        return oracledb.connect(user=usuario, password=senha, dsn=dsn)
    else:
        direto_cfg = oracle_cfg.get('direto', {})
        host = direto_cfg.get('host', '')
        porta = direto_cfg.get('porta', 1521)
        sid = direto_cfg.get('sid', '')
        service_name = direto_cfg.get('service_name', '')
        if service_name:
            dsn = oracledb.makedsn(host, porta, service_name=service_name)
        else:
            dsn = oracledb.makedsn(host, porta, sid=sid)
        return oracledb.connect(user=usuario, password=senha, dsn=dsn)

def check_user_access(userid, empresa):
    if userid == 'VIASOFT':
        return True
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ACESSA_PLUGGY FROM VIASOFT.PUSUARIO WHERE USERID = :p_userid",
            {'p_userid': userid}
        )
        row = cursor.fetchone()
        conn.close()
        return bool(row and row[0] == 'S')
    except Exception:
        return False

def get_table_columns(schema_table):
    parts = schema_table.upper().split('.')
    if len(parts) == 2:
        schema, table = parts[0], parts[1]
    else:
        schema, table = 'VIASOFT', parts[0]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
           FROM ALL_COLUMNS
           WHERE OWNER = :p_owner AND TABLE_NAME = :p_table
           ORDER BY COLUMN_ID""",
        {'p_owner': schema, 'p_table': table}
    )
    colunas = [{'nome': r[0], 'tipo': r[1], 'nullable': r[2]} for r in cursor.fetchall()]
    conn.close()
    return colunas
