from neo4j_manager import Neo4jGraph, Node, Relationship


def main():
    try:
        # Crear una instancia de Neo4jGraph con las credenciales adecuadas
        graph = Neo4jGraph("bolt://127.0.0.1:7687", "neo4j", "password")

        # Crear 4 nodos de "usuarios"
        users = [
            Node("Person", {"name": "Alice", "age": 30, "city": "Wonderland"}),
            Node("Person", {"name": "Bob", "age": 25, "city": "Wonderland"}),
            Node("Person", {"name": "Charlie", "age": 35, "city": "Wonderland"}),
            Node("Person", {"name": "David", "age": 40, "city": "Wonderland"})
        ]

        for user in users:
            print(graph.create_node(user))

        nodes = graph.get_all_nodes("Person")
        print(nodes)


        # Crear 3 nodos de "películas"
        movies = [
            Node("Movie", {"title": "Oscar et la dame rose", "genre": "Sci-Fi"}),
            Node("Movie", {"title": "The Secret Sin", "genre": "Sci-Fi"}),
            Node("Movie", {"title": "Interstellar", "genre": "Sci-Fi"})
        ]

        for movie in movies:
            print(graph.create_node(movie))

        reviews = [
            Node("Review", {"title": "ITS BAD", "rating": 1.5, "content": "So bad, I hate it"}),
            Node("Review", {"title": "Mid", "rating": 3.0, "content": "Meh..."}),
            Node("Review", {"title": "SO GOOD!!", "rating": 10, "content": "Woah so good"}),
            Node("Review", {"title": "Ummm", "rating": 5.1, "content": "idk"}),

            Node("Review", {"title": "Very nice", "rating": 5.1, "content": ":)"}),
            Node("Review", {"title": "Cinema", "rating": 5.1, "content": "You got me... it's cinema"}),
            Node("Review", {"title": "Hello", "rating": 5.1, "content": "world"}),
            Node("Review", {"title": "Nose", "rating": 5.1, "content": "....."}),
            Node("Review", {"title": "Trash", "rating": 5.1, "content": ">:("}),

        ]

        for review in reviews:
            print(graph.create_node(review))

        # Crear relaciones FAVORITE desde cada usuario hacia una película seleccionada al azar
        graph.create_relationship(Relationship(Node("Person", {"name": "Alice"}), Node("Review", {"title": "ITS BAD"}), "MADE_A"))
        graph.create_relationship(Relationship(Node("Person", {"name": "Alice"}), Node("Review", {"title": "SO GOOD!!"}), "MADE_A"))
        graph.create_relationship(Relationship(Node("Person", {"name": "Bob"}), Node("Review", {"title": "Mid"}), "MADE_A"))
        graph.create_relationship(Relationship(Node("Person", {"name": "Charlie"}), Node("Review", {"title": "Ummm"}), "MADE_A"))
        graph.create_relationship(
            Relationship(Node("Person", {"name": "David"}), Node("Review", {"title": "Very nice"}), "MADE_A"))
        graph.create_relationship(
            Relationship(Node("Person", {"name": "Charlie"}), Node("Review", {"title": "Cinema"}), "MADE_A"))
        graph.create_relationship(
            Relationship(Node("Person", {"name": "Bob"}), Node("Review", {"title": "Hello"}), "MADE_A"))
        graph.create_relationship(
            Relationship(Node("Person", {"name": "Charlie"}), Node("Review", {"title": "Nose"}), "MADE_A"))
        graph.create_relationship(
            Relationship(Node("Person", {"name": "Charlie"}), Node("Review", {"title": "Trash"}), "MADE_A"))

        reseñas_alice = graph.get_outgoing_related_nodes(Node("Person", {"name": "Alice"}), "MADE_A")
        print(f"Reseñas hechas por Alice = {reseñas_alice}")

        graph.create_relationship(Relationship(Node("Review", {"title": "ITS BAD"}), Node("Movie", {"title": "Oscar et la dame rose"}), "BELONGS_TO"))
        graph.create_relationship(Relationship(Node("Review", {"title": "SO GOOD!!"}), Node("Movie", {"title": "Oscar et la dame rose"}), "BELONGS_TO"))
        graph.create_relationship(Relationship(Node("Review", {"title": "Ummm"}), Node("Movie", {"title": "Oscar et la dame rose"}), "BELONGS_TO"))
        graph.create_relationship(Relationship(Node("Review", {"title": "Mid"}), Node("Movie", {"title": "The Secret Sin"}), "BELONGS_TO"))

        graph.create_relationship(
            Relationship(Node("Review", {"title": "Very nice"}), Node("Movie", {"title": "Oscar et la dame rose"}),
                         "BELONGS_TO"))
        graph.create_relationship(
            Relationship(Node("Review", {"title": "Cinema"}), Node("Movie", {"title": "Oscar et la dame rose"}),
                         "BELONGS_TO"))
        graph.create_relationship(
            Relationship(Node("Review", {"title": "Hello"}), Node("Movie", {"title": "Oscar et la dame rose"}),
                         "BELONGS_TO"))
        graph.create_relationship(
            Relationship(Node("Review", {"title": "Nose"}), Node("Movie", {"title": "Oscar et la dame rose"}), "BELONGS_TO"))
        graph.create_relationship(
            Relationship(Node("Review", {"title": "Trash"}), Node("Movie", {"title": "Oscar et la dame rose"}), "BELONGS_TO"))

        # Encuentra todas las Reviews pertenecientes a la Película The Matrix
        reseñas = graph.get_incoming_related_nodes("BELONGS_TO", Node("Movie", {"title": "Oscar et la dame rose"}))
        print(f"Reseñas de Oscar et la dame rose = {reseñas}")

        # Filtra los títulos de las Reviews pertenecientes a la Película The Matrix
        titulos_reseñas = [reseña.properties.get('title') for reseña in reseñas]
        print(titulos_reseñas)

        users = []
        for titulo in titulos_reseñas:
            nodo_user = graph.get_incoming_related_nodes("MADE_A", Node("Review", {"title": titulo}))
            users.append(nodo_user)

        print(users)

        print("---------------------------------------------")

        graph.close()
    except Exception as e:
        print(f"Error en la ejecución del programa: {e}")

if __name__ == "__main__":
    main()
