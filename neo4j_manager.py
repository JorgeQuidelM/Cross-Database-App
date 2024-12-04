from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from dataclasses import dataclass
from typing import Callable, Any, List, Dict


@dataclass
class Node:
    label: str
    properties: dict


@dataclass
class Relationship:
    start_node: Node
    end_node: Node
    relationship_type: str


class Neo4jGraph:
    """Clase para interactuar con una base de datos Neo4j."""

    def __init__(self, uri, user, password):
        """Inicializa la conexión a la base de datos Neo4j."""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._verify_connection()
        except ServiceUnavailable as e:
            raise ConnectionError(f"Error al conectar a Neo4j: {e}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al inicializar la conexión: {e}")

    def close(self):
        """Cierra la conexión a la base de datos Neo4j."""
        if self.driver:
            self.driver.close()

    def execute_transaction(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Ejecuta una transacción en la base de datos Neo4j."""
        try:
            with self.driver.session() as session:
                return session.execute_write(func, *args, **kwargs)
        except Neo4jError as neo4j_error:
            raise RuntimeError(f"Error al ejecutar la transacción: {neo4j_error}") from neo4j_error

    def execute_read(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Ejecuta una operación de lectura en la base de datos Neo4j."""
        try:
            with self.driver.session() as session:
                return session.read_transaction(func, *args, **kwargs)
        except Neo4jError as neo4j_error:
            raise RuntimeError(f"Error al ejecutar la operación de lectura: {neo4j_error}") from neo4j_error

    def create_node(self, node: Node):
        """Crea un nodo en la base de datos Neo4j."""
        return self.execute_transaction(self._create_node, node)

    def create_relationship(self, relationship: Relationship):
        """Crea una relación entre dos nodos en la base de datos Neo4j."""
        return self.execute_transaction(self._create_relationship, relationship)

    def delete_node(self, node: Node):
        """Elimina un nodo de la base de datos Neo4j."""
        return self.execute_transaction(self._delete_node, node)

    def delete_relationship(self, relationship: Relationship):
        """Elimina una relación entre dos nodos en la base de datos Neo4j."""
        return self.execute_transaction(self._delete_relationship, relationship)

    def get_all_nodes(self, node_label: str) -> List[Node]:
        """Obtiene todos los nodos de un tipo específico en la base de datos Neo4j."""
        return self.execute_read(self._get_all_nodes, node_label)

    def get_outgoing_related_nodes(self, node: Node, relationship_type: str) -> List[Node]:
        """Obtiene nodos relacionados salientes a un nodo específico en la base de datos Neo4j."""
        return self.execute_read(self._get_outgoing_related_nodes, node, relationship_type)

    def get_incoming_related_nodes(self, relationship_type: str, node_properties: Node) -> List[Node]:
        """Obtiene nodos relacionados entrantes a un nodo específico en la base de datos Neo4j."""
        return self.execute_read(self._get_incoming_related_nodes, relationship_type, node_properties)

    def get_nodes_with_two_step_relationship(self, start_node: Node,
                                             relationship_type_1: str, intermediate_node: str,
                                             relationship_type_2: str, end_node: Node) -> List[Dict[str, Node]]:
        """Obtiene nodos relacionados con propiedades específicas en la base de datos Neo4j."""
        return self.execute_read(self._get_nodes_with_two_step_relationship, start_node,
                                            relationship_type_1, intermediate_node,
                                            relationship_type_2, end_node)

    def _verify_connection(self):
        """Verifica la conexión a la base de datos Neo4j."""
        with self.driver.session() as session:
            session.run("RETURN 1")

    def _node_exists(self, tx, node: Node):
        """Verifica si un nodo existe en la base de datos Neo4j."""
        node_label = node.label
        node_property_key = next(iter(node.properties))
        node_property_value = next(iter(node.properties.values()))

        query = (
            f"MATCH (n:{node_label} {{ {node_property_key}: $node_value }}) "
            "RETURN COUNT(n) AS count"
        )
        result = tx.run(query, node_value=node_property_value)
        return result.single()["count"] > 0

    def _relationship_exists(self, tx, relationship: Relationship):
        """Verifica si una relación existe entre dos nodos en la base de datos Neo4j."""
        start_node_label = relationship.start_node.label
        start_node_property_key = next(iter(relationship.start_node.properties))
        start_node_property_value = next(iter(relationship.start_node.properties.values()))

        end_node_label = relationship.end_node.label
        end_node_property_key = next(iter(relationship.end_node.properties))
        end_node_property_value = next(iter(relationship.end_node.properties.values()))

        query = (
            f"MATCH (start:{start_node_label} {{ {start_node_property_key}: $start_value }})-[r:{relationship.relationship_type}]->"
            f"(end:{end_node_label} {{ {end_node_property_key}: $end_value }}) "
            "RETURN COUNT(r) AS count"
        )
        result = tx.run(query, start_value=start_node_property_value, end_value=end_node_property_value)
        return result.single()["count"] > 0

    def _create_node(self, tx, node: Node):
        """Crea un nodo en la base de datos Neo4j."""
        first_key = next(iter(node.properties))
        first_value = node.properties[first_key]
        if self._node_exists(tx, node):
            return f'Node with {first_key}={first_value} already exists.'

        properties_str = ', '.join([f"{key}: ${key}" for key in node.properties.keys()])
        query = f"CREATE (n:{node.label} {{{properties_str}}}) RETURN n"
        tx.run(query, **node.properties)
        return f'Node with properties {node.properties} of type {node.label} has been created.'

    def _create_relationship(self, tx, relationship: Relationship):
        """Crea una relación entre dos nodos en la base de datos Neo4j."""
        start_node_label = relationship.start_node.label
        start_node_property_key = next(iter(relationship.start_node.properties))
        start_node_property_value = next(iter(relationship.start_node.properties.values()))

        end_node_label = relationship.end_node.label
        end_node_property_key = next(iter(relationship.end_node.properties))
        end_node_property_value = next(iter(relationship.end_node.properties.values()))

        if not self._node_exists(tx, relationship.start_node):
            return f'Node with {start_node_property_key}={start_node_property_value} does not exist.'
        if not self._node_exists(tx, relationship.end_node):
            return f'Node with {end_node_property_key}={end_node_property_value} does not exist.'
        if self._relationship_exists(tx, relationship):
            return f'Relationship between nodes with {start_node_property_key}={start_node_property_value} and {end_node_property_key}={end_node_property_value} already exists.'

        query = (
            f"MERGE (start:{start_node_label} {{ {start_node_property_key}: $start_value }}) "
            f"MERGE (end:{end_node_label} {{ {end_node_property_key}: $end_value }}) "
            f"MERGE (start)-[:{relationship.relationship_type}]->(end) "
            "RETURN start.name + ' and ' + end.name + ' are now connected.'"
        )
        result = tx.run(query, start_value=start_node_property_value, end_value=end_node_property_value)
        return result.single()[0]

    def _delete_node(self, tx, node: Node):
        """Elimina un nodo de la base de datos Neo4j."""
        node_label = node.label
        node_property_key = next(iter(node.properties))
        node_property_value = next(iter(node.properties.values()))

        if not self._node_exists(tx, node):
            return f'No node with {node_property_key}={node_property_value} found with the label "{node_label}".'

        query = (
            f"MATCH (n:{node_label} {{ {node_property_key}: $node_value }}) "
            f"DETACH DELETE n "
        )
        result = tx.run(query, node_value=node_property_value)
        return f'{node_property_value} has been deleted.'

    def _delete_relationship(self, tx, relationship: Relationship):
        """Elimina una relación entre dos nodos en la base de datos Neo4j."""
        start_node_label = relationship.start_node.label
        start_node_property_key = next(iter(relationship.start_node.properties))
        start_node_property_value = next(iter(relationship.start_node.properties.values()))

        end_node_label = relationship.end_node.label
        end_node_property_key = next(iter(relationship.end_node.properties))
        end_node_property_value = next(iter(relationship.end_node.properties.values()))

        if not self._relationship_exists(tx, relationship):
            return (f'No relationship found between nodes with '
                    f'{start_node_property_key}={start_node_property_value} and '
                    f'{end_node_property_key}={end_node_property_value}.')

        query = (
            f"MATCH (start:{start_node_label} {{ {start_node_property_key}: $start_value }})-[r:{relationship.relationship_type}]->"
            f"(end:{end_node_label} {{ {end_node_property_key}: $end_value }}) DELETE r"
        )
        tx.run(query, start_value=start_node_property_value, end_value=end_node_property_value)
        return f'Relationship between nodes with {start_node_property_key}={start_node_property_value} and {end_node_property_key}={end_node_property_value} has been deleted.'

    def _get_all_nodes(self, tx, node_label: str) -> List[Node]:
        """Obtiene todos los nodos de un tipo específico en la base de datos Neo4j."""
        query = f"MATCH (n:{node_label}) RETURN n"
        result = tx.run(query)
        return [Node(label=node_label, properties=dict(record["n"])) for record in result]

    def _get_outgoing_related_nodes(self, tx, node: Node, relationship_type: str) -> List[Node]:
        """Obtiene nodos relacionados salientes a un nodo específico en la base de datos Neo4j."""
        node_label = node.label
        node_property_key = next(iter(node.properties))
        node_property_value = next(iter(node.properties.values()))

        query = (
            f"MATCH (n:{node_label} {{ {node_property_key}: $property_value }})-[r:{relationship_type}]->(m) "
            "RETURN m"
        )
        result = tx.run(query, property_value=node_property_value)
        return [Node(label=list(record["m"].labels)[0], properties=dict(record["m"])) for record in result]

    def _get_incoming_related_nodes(self, tx, relationship_type: str, node: Node) -> List[Node]:
        """Obtiene nodos relacionados entrantes a un nodo específico en la base de datos Neo4j."""
        node_label = node.label
        node_property_key = next(iter(node.properties))
        node_property_value = next(iter(node.properties.values()))

        query = (
            f"MATCH (m)-[r:{relationship_type}]->(n:{node_label} {{ {node_property_key}: $property_value }}) "
            "RETURN m"
        )
        result = tx.run(query, property_value=node_property_value)
        return [Node(label=list(record["m"].labels)[0], properties=dict(record["m"])) for record in result]
