from mongodb_manager import MongoDBClient

uri = "mongodb://localhost:27017/"
database_name = "test_db"
try:
    client = MongoDBClient(uri, database_name)
    # Crear un documento
    document = {"name": "John Doe", "age": 30}
    print(client.create_document("test_collection", document))

    # Leer un documento
    query = {"name": "John Doe"}
    print(client.read_document("test_collection", query))

    # Actualizar un documento
    update = {"age": 31}
    print(client.update_document("test_collection", query, update))

    # Eliminar un documento
    print(client.delete_document("test_collection", query))

    # Cerrar la conexión
    client.close()

except ConnectionError as e:
    print("Pucha")