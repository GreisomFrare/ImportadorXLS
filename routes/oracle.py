from flask import Blueprint, request, jsonify
import db_oracle

oracle_bp = Blueprint('oracle', __name__)

@oracle_bp.route('/auth/check', methods=['POST'])
def auth_check():
    data = request.get_json()
    userid = (data.get('userId') or '').strip().upper()
    empresa = data.get('empresa')
    if not userid:
        return jsonify({'acesso': False, 'motivo': 'Usuário não identificado'})
    acesso = db_oracle.check_user_access(userid, empresa)
    return jsonify({'acesso': acesso})

@oracle_bp.route('/config', methods=['GET'])
def get_config():
    config = db_oracle.load_config()
    oracle_cfg = dict(config.get('oracle', {}))
    if oracle_cfg.get('senha'):
        oracle_cfg['senha'] = '***'
    return jsonify({'oracle': oracle_cfg, 'server': config.get('server', {'porta': 5000})})

@oracle_bp.route('/config', methods=['POST'])
def save_config():
    data = request.get_json()
    config = db_oracle.load_config()
    if 'oracle' in data:
        new_oracle = data['oracle']
        if new_oracle.get('senha') == '***':
            new_oracle['senha'] = config.get('oracle', {}).get('senha', '')
        config['oracle'] = new_oracle
    if 'server' in data:
        config['server'] = data['server']
    db_oracle.save_config(config)
    return jsonify({'ok': True})

@oracle_bp.route('/testar', methods=['POST'])
def testar_conexao():
    try:
        conn = db_oracle.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        conn.close()
        return jsonify({'ok': True, 'mensagem': 'Conexão estabelecida com sucesso'})
    except Exception as e:
        return jsonify({'ok': False, 'mensagem': str(e)})

@oracle_bp.route('/colunas', methods=['GET'])
def get_colunas():
    tabela = request.args.get('tabela', '').strip()
    if not tabela:
        return jsonify({'erro': 'Tabela não informada'}), 400
    try:
        colunas = db_oracle.get_table_columns(tabela)
        return jsonify({'colunas': colunas})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
