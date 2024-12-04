from neo4j_manager import Neo4jGraph, Node, Relationship


def main():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"

    # Crear una instancia de Neo4jGraph
    neo4j_graph = Neo4jGraph(uri, user, password)

    # Crear nodos
    person1 = Node(label="Person", properties={"name": "Alice", "age": 30})
    person2 = Node(label="Person", properties={"name": "Bob", "age": 25})
    company = Node(label="Company", properties={"name": "TechCorp"})

    print(neo4j_graph.create_node(person1))
    print(neo4j_graph.create_node(person2))
    print(neo4j_graph.create_node(company))

    # Crear relaciones
    relationship1 = Relationship(start_node=person1, end_node=company, relationship_type="WORKS_FOR")
    relationship2 = Relationship(start_node=person2, end_node=company, relationship_type="WORKS_FOR")

    print(neo4j_graph.create_relationship(relationship1))
    print(neo4j_graph.create_relationship(relationship2))

    # Obtener todos los nodos de tipo Person
    persons = neo4j_graph.get_all_nodes("Person")
    print("All Persons:", persons)

    # Obtener nodos relacionados salientes a un nodo específico
    related_nodes = neo4j_graph.get_outgoing_related_nodes(person1, "WORKS_FOR")
    print("Related Nodes to Alice:", related_nodes)

    # Obtener nodos relacionados entrantes a un nodo específico
    incoming_related_nodes = neo4j_graph.get_incoming_related_nodes("WORKS_FOR", company)
    print("Incoming Related Nodes to TechCorp:", incoming_related_nodes)

    # Eliminar una relación
    print(neo4j_graph.delete_relationship(relationship1))

    # Eliminar un nodo
    print(neo4j_graph.delete_node(person2))

    # Cerrar la conexión
    neo4j_graph.close()

if __name__ == "__main__":
    main()
