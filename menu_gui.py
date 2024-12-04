import tkinter as tk
from tkinter import ttk
from mongodb_manager import MongoDBClient
from neo4j_manager import Neo4jGraph, Node


class MovieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Viewer")
        self.root.state('zoomed')
        self.root.bind("<Button-1>", self.print_click_coordinates)
        self.root.bind("<Configure>", self.adjust_button_widths)

        self.mongo_client = MongoDBClient("mongodb://localhost:27017/", "imdb")
        self.neo4j_client = Neo4jGraph("bolt://127.0.0.1:7687", "neo4j", "password")

        self.page_size = 25
        self.current_page = 0

        self.setup_ui()
        self.load_movies()

    def setup_ui(self):
        self.create_main_frame()
        self.create_scrollable_frame()
        self.create_button_frame()

    def create_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_scrollable_frame(self):
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Enlazar eventos de desplazamiento del ratón
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

    def create_button_frame(self):
        self.button_frame = tk.Frame(self.root)
        self.button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.prev_page)
        self.prev_button.grid(row=0, column=0, sticky="ew")

        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_page)
        self.next_button.grid(row=0, column=1, sticky="ew")

    def load_movies(self):
        movies = self.mongo_client.fetch_documents_with_limit("movies", self.current_page * self.page_size, self.page_size)
        self.clear_scrollable_frame()

        if not movies:
            self.display_no_records_message()
            return

        self.populate_movies(movies)
        self.adjust_button_widths()

    def clear_scrollable_frame(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def display_no_records_message(self):
        label = tk.Label(self.scrollable_frame, text="No more records.")
        label.pack()

    def populate_movies(self, movies):
        for idx, movie in enumerate(movies, start=self.current_page * self.page_size + 1):
            movie_display = {k: v for k, v in movie.items() if k != '_id'}
            self.create_movie_button(idx, movie_display)

        self.configure_scrollable_frame_weights(len(movies))

    def create_movie_button(self, idx, movie_display):
        record_button = tk.Button(
            self.scrollable_frame,
            text=f"{idx}. {movie_display.get('TITLE', 'Sin título')}",
            font=("Helvetica", 12, "bold"),
            command=lambda movie=movie_display: self.show_movie_details(movie),
            bd=0,
            relief=tk.FLAT,
            height=10
        )
        record_button.grid(row=idx-1, column=0, sticky="ew", pady=5, padx=10)

        if (idx - 1) % 2 == 0:
            record_button.configure(bg='#ffffff')

    def configure_scrollable_frame_weights(self, num_movies):
        for i in range(num_movies):
            self.scrollable_frame.grid_rowconfigure(i, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def adjust_button_widths(self, event=None):
        window_width = self.root.winfo_width()
        button_width = int(window_width / 10)
        for widget in self.scrollable_frame.winfo_children():
            widget.config(width=button_width)

    def show_movie_details(self, movie):
        print(f"Showing details for movie: {movie}")
        self.hide_main_frame()
        self.create_details_frame(movie)

    def hide_main_frame(self):
        self.main_frame.grid_forget()
        self.button_frame.grid_forget()

    def create_details_frame(self, movie):
        self.details_frame = tk.Frame(self.root)
        self.details_frame.grid(row=0, column=0, sticky="nsew")

        self.create_details_scrollable_frame()
        self.populate_movie_details(movie)

    def create_details_scrollable_frame(self):
        self.details_canvas = tk.Canvas(self.details_frame)
        self.details_scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=self.details_canvas.yview)
        self.details_scrollable_frame = ttk.Frame(self.details_canvas)

        self.details_scrollable_frame.bind("<Configure>", lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all")))
        self.details_canvas.create_window((0, 0), window=self.details_scrollable_frame, anchor="nw")
        self.details_canvas.configure(yscrollcommand=self.details_scrollbar.set)

        self.details_canvas.grid(row=0, column=0, sticky="nsew")
        self.details_scrollbar.grid(row=0, column=1, sticky="ns")

        self.details_frame.grid_rowconfigure(0, weight=1)
        self.details_frame.grid_columnconfigure(0, weight=1)

        # Enlazar eventos de desplazamiento del ratón
        self.details_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.details_canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.details_canvas.bind_all("<Button-5>", self.on_mousewheel)

    def populate_movie_details(self, movie):
        title = movie['TITLE']
        reviews = self.neo4j_client.get_incoming_related_nodes("BELONGS_TO", Node("Movie", {"title": title}))

        row_index = self.display_movie_info(movie, row_index=0)
        row_index = self.display_reviews(reviews, row_index)
        self.create_back_button(row_index)

    def display_movie_info(self, movie, row_index):
        for key, value in movie.items():
            if key != '_id':
                label = tk.Label(self.details_scrollable_frame, text=f"{key}: {value}", wraplength=600, justify="left")
                label.grid(row=row_index, column=0, sticky="ew", padx=5, pady=2)
                row_index += 1
        return row_index

    def display_reviews(self, reviews, row_index):
        reviews_label = tk.Label(self.details_scrollable_frame, text="Reviews:", font=("Helvetica", 12, "bold"))
        reviews_label.grid(row=row_index, column=0, sticky="ew", padx=5, pady=10)
        row_index += 1

        for review in reviews:
            row_index = self.create_review_frame(review, row_index)

        return row_index

    def create_review_frame(self, review, row_index):
        review_frame = tk.Frame(self.details_scrollable_frame, bd=1, relief=tk.SUNKEN)
        review_frame.grid(row=row_index, column=0, sticky="ew", padx=5, pady=5)
        review_frame.grid_columnconfigure(0, weight=1)

        self.create_review_labels(review_frame, review)
        row_index += 1
        return row_index

    def create_review_labels(self, review_frame, review):
        title_label = tk.Label(review_frame, text=f"Title: {review.properties['title']}", wraplength=600, justify="left")
        title_label.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        rating_label = tk.Label(review_frame, text=f"Rating: {review.properties['rating']}", wraplength=600, justify="left")
        rating_label.grid(row=1, column=0, sticky="ew", padx=5, pady=2)

        content_label = tk.Label(review_frame, text=f"Content: {review.properties['content']}", wraplength=600, justify="left")
        content_label.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    def create_back_button(self, row_index):
        back_button = tk.Button(self.details_scrollable_frame, text="Back to List", command=self.back_to_list)
        back_button.grid(row=row_index, column=0, pady=10)

    def back_to_list(self):
        print("Returning to movie list")
        self.details_frame.destroy()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

    def next_page(self):
        print("Next page")
        if len(self.mongo_client.fetch_documents_with_limit("movies", (self.current_page + 1) * self.page_size, 1)) > 0:
            self.current_page += 1
            self.load_movies()

    def prev_page(self):
        print("Previous page")
        if self.current_page > 0:
            self.current_page -= 1
            self.load_movies()

    def print_click_coordinates(self, event):
        print(f"Click coordinates: x={event.x}, y={event.y}")

    def on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            self.details_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            if event.num == 5:
                self.canvas.yview_scroll(1, "units")
                self.details_canvas.yview_scroll(1, "units")
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
                self.details_canvas.yview_scroll(-1, "units")


if __name__ == "__main__":
    root = tk.Tk()
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    app = MovieApp(root)
    root.mainloop()
