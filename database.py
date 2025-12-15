"""
Módulo de banco de dados para integração com Verl.ia bot_databases.
Use este módulo para persistir dados do seu bot de forma centralizada.

LIMITES POR PLANO:
- Free: Não pode usar banco de dados
- Pro: 100 linhas por banco de dados
- Pro Master: Ilimitado
"""

import os
import json
from typing import Any, Optional, List, Dict, Tuple
from supabase import create_client, Client

# Initialize Supabase client
_supabase_url = os.getenv('SUPABASE_URL')
_supabase_key = os.getenv('SUPABASE_KEY')
_bot_id = os.getenv('BOT_ID')
_supabase: Optional[Client] = None
_user_plan: Optional[str] = None
_plan_limits = {
    'free': {'can_use': False, 'max_rows': 0},
    'pro': {'can_use': True, 'max_rows': 100},
    'pro_master': {'can_use': True, 'max_rows': -1},  # -1 = ilimitado
    'premium': {'can_use': True, 'max_rows': -1},
}

class DatabaseAccessError(Exception):
    """Erro de acesso ao banco de dados devido a restrições de plano."""
    pass

def _get_client() -> Client:
    global _supabase
    if _supabase is None:
        if not _supabase_url or not _supabase_key:
            raise Exception("SUPABASE_URL e SUPABASE_KEY não configurados")
        _supabase = create_client(_supabase_url, _supabase_key)
    return _supabase

def _get_user_plan() -> Tuple[str, dict]:
    """
    Obtém o plano do usuário dono do bot.
    Retorna (plan_name, plan_limits)
    """
    global _user_plan
    
    if _user_plan is not None:
        return _user_plan, _plan_limits.get(_user_plan, _plan_limits['free'])
    
    try:
        client = _get_client()
        
        # Get bot owner
        bot_response = client.table('bots').select('user_id').eq('id', _bot_id).single().execute()
        if not bot_response.data:
            return 'free', _plan_limits['free']
        
        user_id = bot_response.data['user_id']
        
        # Get user profile with plan
        profile_response = client.table('profiles').select('plan').eq('user_id', user_id).single().execute()
        if not profile_response.data:
            return 'free', _plan_limits['free']
        
        _user_plan = profile_response.data.get('plan', 'free')
        return _user_plan, _plan_limits.get(_user_plan, _plan_limits['free'])
    except Exception as e:
        print(f"Erro ao verificar plano: {e}")
        return 'free', _plan_limits['free']

def _check_plan_access(operation: str = "usar banco de dados") -> dict:
    """
    Verifica se o plano permite a operação.
    Levanta DatabaseAccessError se não permitido.
    """
    plan_name, limits = _get_user_plan()
    
    if not limits['can_use']:
        raise DatabaseAccessError(
            f"❌ Plano '{plan_name}' não permite {operation}. "
            f"Faça upgrade para Pro ou Pro Master em verl.ia/pricing"
        )
    
    return limits

def get_database(name: str) -> Optional[Dict]:
    """
    Obtém um banco de dados pelo nome.
    Retorna o objeto do banco ou None se não existir.
    """
    try:
        _check_plan_access("visualizar banco de dados")
        client = _get_client()
        response = client.table('bot_databases').select('*').eq('bot_id', _bot_id).eq('name', name).single().execute()
        return response.data
    except DatabaseAccessError as e:
        print(str(e))
        return None
    except Exception as e:
        print(f"Erro ao obter banco de dados: {e}")
        return None

def create_database(name: str) -> Optional[Dict]:
    """
    Cria um novo banco de dados para o bot.
    O limite de linhas é definido automaticamente pelo plano.
    """
    try:
        limits = _check_plan_access("criar banco de dados")
        max_rows = limits['max_rows'] if limits['max_rows'] > 0 else 999999
        
        client = _get_client()
        response = client.table('bot_databases').insert({
            'bot_id': _bot_id,
            'name': name,
            'data': [],
            'max_rows': max_rows,
            'row_count': 0
        }).execute()
        return response.data[0] if response.data else None
    except DatabaseAccessError as e:
        print(str(e))
        return None
    except Exception as e:
        print(f"Erro ao criar banco de dados: {e}")
        return None

def get_or_create_database(name: str) -> Optional[Dict]:
    """
    Obtém um banco de dados existente ou cria um novo.
    """
    db = get_database(name)
    if db is None:
        db = create_database(name)
    return db

def get_all_data(db_name: str) -> List[Dict]:
    """
    Obtém todos os dados de um banco de dados.
    """
    db = get_database(db_name)
    if db and db.get('data'):
        return db['data']
    return []

def add_data(db_name: str, item: Dict) -> bool:
    """
    Adiciona um item ao banco de dados.
    Respeita os limites de linhas do plano.
    """
    try:
        limits = _check_plan_access("adicionar dados")
        
        db = get_or_create_database(db_name)
        if db is None:
            return False
        
        data = db.get('data', [])
        row_count = db.get('row_count', 0)
        max_rows = limits['max_rows']
        
        # Check limit (unless unlimited)
        if max_rows > 0 and row_count >= max_rows:
            print(f"❌ Limite de {max_rows} registros atingido para plano atual. Faça upgrade para mais espaço.")
            return False
        
        data.append(item)
        
        client = _get_client()
        client.table('bot_databases').update({
            'data': data,
            'row_count': len(data)
        }).eq('id', db['id']).execute()
        
        return True
    except DatabaseAccessError as e:
        print(str(e))
        return False
    except Exception as e:
        print(f"Erro ao adicionar dados: {e}")
        return False

def update_data(db_name: str, index: int, item: Dict) -> bool:
    """
    Atualiza um item no banco de dados pelo índice.
    """
    try:
        _check_plan_access("atualizar dados")
        
        db = get_database(db_name)
        if db is None:
            return False
        
        data = db.get('data', [])
        if index < 0 or index >= len(data):
            return False
        
        data[index] = item
        
        client = _get_client()
        client.table('bot_databases').update({
            'data': data
        }).eq('id', db['id']).execute()
        
        return True
    except DatabaseAccessError as e:
        print(str(e))
        return False
    except Exception as e:
        print(f"Erro ao atualizar dados: {e}")
        return False

def delete_data(db_name: str, index: int) -> bool:
    """
    Remove um item do banco de dados pelo índice.
    """
    try:
        _check_plan_access("deletar dados")
        
        db = get_database(db_name)
        if db is None:
            return False
        
        data = db.get('data', [])
        if index < 0 or index >= len(data):
            return False
        
        data.pop(index)
        
        client = _get_client()
        client.table('bot_databases').update({
            'data': data,
            'row_count': len(data)
        }).eq('id', db['id']).execute()
        
        return True
    except DatabaseAccessError as e:
        print(str(e))
        return False
    except Exception as e:
        print(f"Erro ao deletar dados: {e}")
        return False

def find_data(db_name: str, key: str, value: Any) -> List[Dict]:
    """
    Busca itens que correspondem a um critério.
    """
    data = get_all_data(db_name)
    return [item for item in data if item.get(key) == value]

def find_index(db_name: str, key: str, value: Any) -> int:
    """
    Encontra o índice do primeiro item que corresponde ao critério.
    Retorna -1 se não encontrado.
    """
    data = get_all_data(db_name)
    for i, item in enumerate(data):
        if item.get(key) == value:
            return i
    return -1

def clear_database(db_name: str) -> bool:
    """
    Limpa todos os dados de um banco de dados.
    """
    try:
        _check_plan_access("limpar banco de dados")
        
        db = get_database(db_name)
        if db is None:
            return False
        
        client = _get_client()
        client.table('bot_databases').update({
            'data': [],
            'row_count': 0
        }).eq('id', db['id']).execute()
        
        return True
    except DatabaseAccessError as e:
        print(str(e))
        return False
    except Exception as e:
        print(f"Erro ao limpar banco de dados: {e}")
        return False

def count_data(db_name: str) -> int:
    """
    Conta quantos registros existem no banco de dados.
    """
    data = get_all_data(db_name)
    return len(data)

def exists(db_name: str, key: str, value: Any) -> bool:
    """
    Verifica se existe um item com a chave/valor especificados.
    """
    return len(find_data(db_name, key, value)) > 0

def delete_by_key(db_name: str, key: str, value: Any) -> bool:
    """
    Deleta o primeiro item que corresponde à chave/valor.
    Retorna True se deletou, False se não encontrou.
    """
    idx = find_index(db_name, key, value)
    if idx >= 0:
        return delete_data(db_name, idx)
    return False

def delete_all_by_key(db_name: str, key: str, value: Any) -> int:
    """
    Deleta TODOS os itens que correspondem à chave/valor.
    Retorna quantidade de itens deletados.
    """
    try:
        _check_plan_access("deletar dados")
        
        db = get_database(db_name)
        if db is None:
            return 0
        
        data = db.get('data', [])
        original_count = len(data)
        new_data = [item for item in data if item.get(key) != value]
        deleted_count = original_count - len(new_data)
        
        if deleted_count > 0:
            client = _get_client()
            client.table('bot_databases').update({
                'data': new_data,
                'row_count': len(new_data)
            }).eq('id', db['id']).execute()
        
        return deleted_count
    except DatabaseAccessError as e:
        print(str(e))
        return 0
    except Exception as e:
        print(f"Erro ao deletar dados: {e}")
        return 0

def update_by_key(db_name: str, key: str, value: Any, new_item: Dict) -> bool:
    """
    Atualiza o primeiro item que corresponde à chave/valor.
    """
    idx = find_index(db_name, key, value)
    if idx >= 0:
        return update_data(db_name, idx, new_item)
    return False

def upsert_data(db_name: str, key: str, value: Any, item: Dict) -> bool:
    """
    Atualiza se existir, insere se não existir (upsert).
    """
    idx = find_index(db_name, key, value)
    if idx >= 0:
        return update_data(db_name, idx, item)
    else:
        return add_data(db_name, item)

def list_databases() -> List[str]:
    """
    Lista todos os bancos de dados do bot.
    """
    try:
        _check_plan_access("listar bancos de dados")
        
        client = _get_client()
        response = client.table('bot_databases').select('name').eq('bot_id', _bot_id).execute()
        return [db['name'] for db in (response.data or [])]
    except DatabaseAccessError as e:
        print(str(e))
        return []
    except Exception as e:
        print(f"Erro ao listar bancos de dados: {e}")
        return []

def delete_database(db_name: str) -> bool:
    """
    Deleta completamente um banco de dados.
    """
    try:
        _check_plan_access("deletar banco de dados")
        
        db = get_database(db_name)
        if db is None:
            return False
        
        client = _get_client()
        client.table('bot_databases').delete().eq('id', db['id']).execute()
        
        return True
    except DatabaseAccessError as e:
        print(str(e))
        return False
    except Exception as e:
        print(f"Erro ao deletar banco de dados: {e}")
        return False

def get_plan_info() -> Dict:
    """
    Retorna informações sobre o plano atual e seus limites.
    """
    plan_name, limits = _get_user_plan()
    return {
        'plan': plan_name,
        'can_use_database': limits['can_use'],
        'max_rows': limits['max_rows'] if limits['max_rows'] > 0 else 'ilimitado'
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 📚 DOCUMENTAÇÃO COMPLETA
# ═══════════════════════════════════════════════════════════════════════════════
#
# FUNÇÕES DISPONÍVEIS:
#
# 📊 CRUD BÁSICO:
#   - add_data(db_name, item)           → Adiciona um item
#   - get_all_data(db_name)             → Lista todos os itens
#   - update_data(db_name, index, item) → Atualiza item por índice
#   - delete_data(db_name, index)       → Deleta item por índice
#   - clear_database(db_name)           → Limpa todos os dados
#
# 🔍 BUSCA:
#   - find_data(db_name, key, value)    → Busca itens por chave/valor
#   - find_index(db_name, key, value)   → Encontra índice do item
#   - exists(db_name, key, value)       → Verifica se existe
#   - count_data(db_name)               → Conta registros
#
# ✏️ OPERAÇÕES AVANÇADAS:
#   - delete_by_key(db_name, key, val)  → Deleta primeiro item encontrado
#   - delete_all_by_key(db_name, k, v)  → Deleta TODOS que correspondem
#   - update_by_key(db_name, k, v, new) → Atualiza primeiro encontrado
#   - upsert_data(db_name, k, v, item)  → Atualiza ou insere
#
# 🗂️ GERENCIAMENTO:
#   - get_database(db_name)             → Obtém objeto do banco
#   - create_database(db_name)          → Cria novo banco
#   - list_databases()                  → Lista bancos existentes
#   - delete_database(db_name)          → Deleta banco completo
#   - get_plan_info()                   → Info do plano atual
#
# ═══════════════════════════════════════════════════════════════════════════════
# 💡 EXEMPLOS DE USO
# ═══════════════════════════════════════════════════════════════════════════════
#
# from database import (
#     add_data, get_all_data, find_data, exists, 
#     delete_by_key, upsert_data, get_plan_info
# )
#
# # ─── Verificar plano ───
# info = get_plan_info()
# print(f"Plano: {info['plan']}, Limite: {info['max_rows']} linhas")
#
# # ─── Sistema de banimento ───
# add_data('banned_users', {
#     'user_id': '123456789', 
#     'reason': 'spam', 
#     'banned_by': 'admin',
#     'banned_at': '2024-01-15'
# })
#
# # Verificar se usuário está banido
# if exists('banned_users', 'user_id', '123456789'):
#     print("Usuário está banido!")
#
# # Remover ban
# delete_by_key('banned_users', 'user_id', '123456789')
#
# # ─── Sistema de economia ───
# # Adicionar ou atualizar saldo
# upsert_data('economy', 'user_id', '123', {
#     'user_id': '123',
#     'balance': 1000,
#     'last_daily': '2024-01-15'
# })
#
# # ─── Sistema de warns ───
# add_data('warns', {
#     'user_id': '123',
#     'reason': 'linguagem inapropriada',
#     'warn_count': 1
# })
#
# # Contar warns do usuário
# warns = find_data('warns', 'user_id', '123')
# total_warns = len(warns)
#
# ═══════════════════════════════════════════════════════════════════════════════
