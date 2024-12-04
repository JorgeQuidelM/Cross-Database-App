from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import time
from typing import Dict, Any, Optional, List

class MongoDBClient:
    def __init__(self, uri: str, database_name: str, retries: int = 2, delay: float = 0.5):
        """
        Constructor de la clase MongoDBClient.

        Parámetros:
        uri (str): La URI para conectarse a la base de datos MongoDB.
        database_name (str): El nombre de la base de datos a la que se conectará.
        retries (int): Número de intentos de reconexión.
        delay (float): Tiempo en segundos entre intentos de reconexión.

        Intenta establecer una conexión con la base de datos y verifica su disponibilidad.
        """
        self.client = None
        self.db = None
        for attempt in range(retries):
            try:
                self.client = MongoClient(uri)
                self.db = self.client[database_name]
                # Verificar la conexión ejecutando una operación simple.
                self.db.command("ping")
                break  # Exit loop if successful
            except ConnectionFailure as e:
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                    continue
                raise ConnectionError(f"Error al conectar a MongoDB después de {retries} intentos: {e}")
            except Exception as e:
                raise RuntimeError(f"Error inesperado al inicializar la conexión: {e}")

    def close_connection(self):
        """Cierra la conexión con la base de datos."""
        if self.client:
            self.client.close()

    def insert_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Inserta un documento en la colección especificada."""
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return f'Documento con _id {result.inserted_id} ha sido creado.'
        except OperationFailure as e:
            raise RuntimeError(f"Error al insertar el documento: {e}")

    def fetch_document(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recupera un documento de la colección especificada."""
        try:
            collection = self.db[collection_name]
            document = collection.find_one(query)
            return document
        except OperationFailure as e:
            raise RuntimeError(f"Error al recuperar el documento: {e}")

    def fetch_documents_with_limit(self, collection_name: str, skip: int, limit: int) -> List[Dict]:
        """Recupera documentos de la colección especificada con un límite."""
        try:
            collection = self.db[collection_name]
            return list(collection.find().skip(skip).limit(limit))
        except OperationFailure as e:
            raise RuntimeError(f"Error al recuperar los documentos: {e}")

    def update_document(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> str:
        """Actualiza un documento en la colección especificada."""
        try:
            collection = self.db[collection_name]
            result = collection.update_one(query, {"$set": update})
            if result.modified_count > 0:
                return f'Documento coincidente con {query} ha sido actualizado.'
            else:
                return f'No se encontró ningún documento coincidente con {query} para actualizar.'
        except OperationFailure as e:
            raise RuntimeError(f"Error al actualizar el documento: {e}")

    def delete_document(self, collection_name: str, query: Dict[str, Any]) -> str:
        """Elimina un documento de la colección especificada."""
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            if result.deleted_count > 0:
                return f'Documento coincidente con {query} ha sido eliminado.'
            else:
                return f'No se encontró ningún documento coincidente con {query} para eliminar.'
        except OperationFailure as e:
            raise RuntimeError(f"Error al eliminar el documento: {e}")
