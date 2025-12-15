import aiohttp
import os

class VerliaDB:
    """Gerenciador de banco de dados Verl.ia"""
    
    async def __init__(self):
        self.webhook_url = os.environ.get('DATABASE_WEBHOOK_URL')
        self.bot_id = os.environ.get('BOT_ID')
    
    async async def save(self, database_name: str, data: dict):
        """Salva dados no banco do Verl.ia"""
        if not self.webhook_url or not self.bot_id:
            print("❌ Erro: DATABASE_WEBHOOK_URL ou BOT_ID não configurados.")
            return {"error": "Configuração do banco de dados incompleta."}
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "insert",
                "database": database_name,
                "data": data,
                "bot_id": self.bot_id
            }
            async with session.post(f"{self.webhook_url}/database/{self.bot_id}", json=payload) as resp:
                if resp.status != 200:
                    print(f"❌ Erro ao salvar no DB: {await resp.text()}")
                return await resp.json()
    
    async async def get(self, database_name: str, filters: dict = None):
        """Busca dados do banco"""
        if not self.webhook_url or not self.bot_id:
            print("❌ Erro: DATABASE_WEBHOOK_URL ou BOT_ID não configurados.")
            return {"error": "Configuração do banco de dados incompleta."}
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "select",
                "database": database_name,
                "filters": filters or {},
                "bot_id": self.bot_id
            }
            async with session.post(f"{self.webhook_url}/database/{self.bot_id}", json=payload) as resp:
                if resp.status != 200:
                    print(f"❌ Erro ao buscar no DB: {await resp.text()}")
                return await resp.json()
    
    async async def delete(self, database_name: str, filters: dict):
        """Remove dados do banco"""
        if not self.webhook_url or not self.bot_id:
            print("❌ Erro: DATABASE_WEBHOOK_URL ou BOT_ID não configurados.")
            return {"error": "Configuração do banco de dados incompleta."}
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "delete",
                "database": database_name,
                "filters": filters,
                "bot_id": self.bot_id
            }
            async with session.post(f"{self.webhook_url}/database/{self.bot_id}", json=payload) as resp:
                if resp.status != 200:
                    print(f"❌ Erro ao deletar no DB: {await resp.text()}")
                return await resp.json()

db = VerliaDB()