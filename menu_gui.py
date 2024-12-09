import tkinter as tk
from tkinter import ttk, messagebox
from mongodb_manager import MongoDBClient
from neo4j_manager import Neo4jGraph, Node


class MovieApp:
    PAGE_SIZE = 25
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "imdb"
    NEO4J_URI = "bolt://127.0.0.1:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"

    def __init__(self, root):
        self.root = root
        self.root.title("Movie Viewer")
        self.root.state('zoomed')

        self.mongo_client = None
        self.neo4j_client = None

        self.current_page = 0
        self.current_movie = None

        self.setup_ui()
        self.connect_to_mongo()
        self.load_movie_list()

    def setup_ui(self):
        self.main_page = ttk.Frame(self.root)
        self.initialize_main_top_bar()
        self.initialize_movie_list()
        self.initialize_pagination_controls()
        self.main_page.pack(fill=tk.BOTH, expand=True)

    def initialize_main_top_bar(self):
        top_frame = ttk.Frame(self.main_page, height=50, relief="raised", padding=10)
        top_frame.pack(fill=tk.BOTH)

        ttk.Label(top_frame, text="Películas en IMDB").pack(side=tk.LEFT, pady=5)

        self.retry_mongo_button = ttk.Button(top_frame, text="Reintentar conexión con MongoDB", command=self.retry_mongo_connection)
        self.retry_mongo_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def initialize_movie_list(self):
        scrollable_frame_container, self.movies_frame = self.create_scrollable_frame(self.main_page)
        scrollable_frame_container.pack(fill=tk.BOTH, expand=True)

    def initialize_pagination_controls(self):
        self.main_buttons_frame = ttk.Frame(self.main_page, height=100, relief="sunken")
        self.main_buttons_frame.pack(fill=tk.X)

        prev_button = ttk.Button(self.main_buttons_frame, text="Anterior", command=self.prev_page)
        prev_button.pack(side=tk.LEFT, padx=5, pady=5)

        next_button = ttk.Button(self.main_buttons_frame, text="Siguiente", command=self.next_page)
        next_button.pack(side=tk.LEFT, padx=5, pady=5)

    def create_scrollable_frame(self, container):
        frame = ttk.Frame(container)
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return frame, scrollable_frame

    def connect_to_mongo(self):
        try:
            self.mongo_client = MongoDBClient(self.MONGO_URI, self.MONGO_DB)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to MongoDB: {e}")
            self.mongo_client = None

    def load_movie_list(self):
        if not self.mongo_client:
            self.retry_mongo_button.pack()
            return

        movies = self.fetch_movies()
        self.clear_movie_list()

        if not movies:
            messagebox.showwarning("Database Error", "No movies found")
            self.retry_mongo_button.pack()
            return

        self.retry_mongo_button.forget()
        self.display_movie_list(movies)

    def fetch_movies(self):
        try:
            collection = "movies"
            skip = self.current_page * self.PAGE_SIZE
            limit = self.PAGE_SIZE
            return self.mongo_client.fetch_documents_with_limit(collection, skip, limit)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch movies: {e}")
            return []

    def clear_movie_list(self):
        for widget in self.movies_frame.winfo_children():
            widget.destroy()

    def display_movie_list(self, movies):
        movie_index = self.current_page * self.PAGE_SIZE + 1

        for movie in movies:
            movie_details = {key: value for key, value in movie.items() if key != '_id'}
            self.create_movie_button(movie_index, movie_details, self.movies_frame)
            movie_index += 1

    def create_movie_button(self, index, movie, frame):
        button = ttk.Button(frame,
                            text=f"{index}. {movie.get('TITLE', 'Sin título')}",
                            command=lambda: self.show_movie_details(movie),
                            padding=40)
        button.pack(pady=5)

    def show_movie_details(self, movie):
        self.current_movie = movie
        self.setup_details_ui()
        self.connect_to_neo4j()
        self.load_reviews()

    def setup_details_ui(self):
        self.main_page.pack_forget()

        self.details_page = ttk.Frame(self.root)
        self.initialize_details_top_bar()
        self.initialize_movie_details()
        self.initialize_movie_reviews()
        self.details_page.pack(fill=tk.BOTH, expand=True)

    def initialize_details_top_bar(self):
        top_frame = ttk.Frame(self.details_page, height=50, relief="raised", padding=10)
        top_frame.pack(fill=tk.BOTH)

        back_button = ttk.Button(top_frame, text="Volver atrás", command=self.go_back_to_main)
        back_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.retry_neo4j_button = ttk.Button(top_frame, text="Reintentar conexión con Neo4j", command=self.retry_neo4j_connection)
        self.retry_neo4j_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def initialize_movie_details(self):
        self.movie_details_frame = ttk.Frame(self.details_page)
        self.display_movie_details()
        self.movie_details_frame.pack(fill=tk.BOTH)

    def initialize_movie_reviews(self):
        scrollable_frame_container, self.scrollable_reviews_frame = self.create_scrollable_frame(self.details_page)
        scrollable_frame_container.pack(fill=tk.BOTH, expand=True)

    def display_movie_details(self):
        movie = self.current_movie
        for key, value in movie.items():
            if key == '_id':
                continue
            ttk.Label(self.movie_details_frame, text=f"{key}: {value}", wraplength=600, justify="left").pack(pady=10)

    def connect_to_neo4j(self):
        try:
            self.neo4j_client = Neo4jGraph(self.NEO4J_URI, self.NEO4J_USER, self.NEO4J_PASSWORD)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to Neo4j: {e}")
            self.neo4j_client = None

    def load_reviews(self):
        if not self.neo4j_client:
            self.retry_neo4j_button.pack()
            return

        title = self.current_movie['TITLE']
        reviews = self.fetch_reviews(title)
        self.retry_neo4j_button.forget()

        if not reviews:
            return

        self.display_reviews(reviews)

    def fetch_reviews(self, title):
        try:
            relationship = "BELONGS_TO"
            node = Node("Movie", {"title": title})
            return self.neo4j_client.get_incoming_related_nodes(relationship, node)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch reviews: {e}")
            return []

    def display_reviews(self, reviews):
        reviews_label = ttk.Label(self.scrollable_reviews_frame, text="Reviews:", font=("Helvetica", 12, "bold"))
        reviews_label.pack()

        for review in reviews:
            self.create_review_frame(review)

    def create_review_frame(self, review):
        review_frame = ttk.Frame(self.scrollable_reviews_frame, relief=tk.SUNKEN, padding=40)
        review_frame.pack()
        self.create_review_labels(review_frame, review)

    def create_review_labels(self, review_frame, review):
        review_title = review.properties['title']
        title_label = ttk.Label(review_frame, text=f"Title: {review_title}", wraplength=600, justify="left")
        title_label.pack()

        review_rating = review.properties['rating']
        rating_label = ttk.Label(review_frame, text=f"Rating: {review_rating}", wraplength=600, justify="left")
        rating_label.pack()

        review_content = review.properties['content']
        content_label = ttk.Label(review_frame, text=f"Content: {review_content}", wraplength=600, justify="left")
        content_label.pack()

    def retry_mongo_connection(self):
        self.connect_to_mongo()
        self.load_movie_list()

    def retry_neo4j_connection(self):
        self.connect_to_neo4j()
        self.load_reviews()

    def go_back_to_main(self):
        self.details_page.pack_forget()
        self.main_page.pack(fill=tk.BOTH, expand=True)

    def next_page(self):
        if not self.mongo_client:
            messagebox.showerror("Connection Error", "MongoDB connection not founded")
            return

        try:
            if self.has_more_movies():
                self.current_page += 1
                self.load_movie_list()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch movies: {e}")

    def has_more_movies(self):
        next_page_index = (self.current_page + 1) * self.PAGE_SIZE
        movies = self.fetch_movies_for_next_page(next_page_index)
        return len(movies) > 0

    def fetch_movies_for_next_page(self, start_index):
        return self.mongo_client.fetch_documents_with_limit("movies", start_index, 1)

    def prev_page(self):
        if not self.mongo_client:
            messagebox.showerror("Connection Error", "MongoDB connection not founded")
            return
        try:
            if self.current_page > 0:
                self.current_page -= 1
                self.load_movie_list()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch movies: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MovieApp(root)
    root.mainloop()
