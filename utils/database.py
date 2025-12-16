import aiohttp
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

"""Verl.ia Database - Conexão com banco de dados real"""

class VerliaDB:
   """Classe VerliaDB."""
    """Cliente para o banco de dados da Verl.ia"""
    
    def __init__(self):
        self.url = "https://amqhmgatgweklzvcfdiy.supabase.co/functions/v1/bot-webhook"
        self.bot_id = os.environ.get('BOT_ID', '149de6c3-6a87-44de-ab5f-4b960c7714fe')
    
    async def _request(self, action: str, database: str, data: Dict = None, filters: Dict = None) -> Dict:
        """Faz requisição ao banco de dados"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": action,
                "database": database,
                "bot_id": self.bot_id,
                "data": data or {},
                "filters": filters or {}
            }
            async with session.post(
                f"{self.url}/database/{self.bot_id}",
                json=payload
            ) as response:
                response.raise_for_status() # Levanta um erro para respostas HTTP ruins
                return await response.json()
    
    async def insert(self, database: str, data: Dict) -> Dict:
        """Insere um registro no banco"""
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        return await self._request("insert", database, data=data)
    
    async def find(self, database: str, filters: Dict = None) -> List[Dict]:
        """Busca registros no banco"""
        result = await self._request("select", database, filters=filters)
        return result.get("data", [])
    
    async def find_one(self, database: str, filters: Dict) -> Optional[Dict]:
        """Busca um único registro"""
        results = await self.find(database, filters)
        return results[0] if results else None
    
    async def update(self, database: str, filters: Dict, data: Dict) -> Dict:
        """Atualiza registros no banco"""
        data["updated_at"] = datetime.utcnow().isoformat()
        return await self._request("update", database, data=data, filters=filters)
    
    async def delete(self, database: str, filters: Dict) -> Dict:
        """Deleta registros do banco"""
        return await self._request("delete", database, filters=filters)
    
    async def count(self, database: str, filters: Dict = None) -> int:
        """Conta registros no banco"""
        results = await self.find(database, filters)
        return len(results)

# Instância global do banco de dados
db = VerliaDB()