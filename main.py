import tkinter as tk
import random
import vlc
import customtkinter as ctk
from tkinter import filedialog , messagebox
from tinytag import TinyTag
import sqlite3  # Import SQLite module

ctk.set_appearance_mode("light")  

# VLC player instance
instance = vlc.Instance()
player = instance.media_player_new()
playlist = []
current_index = None
running_flag = [False]  # Controls the visualizer

# SQLite Database Setup
def setup_database():
    try:
        conn = sqlite3.connect("playlist.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                title TEXT,
                album TEXT,
                artist TEXT,
                bitrate REAL
            )
        """)
        conn.commit()
        print("Database setup completed successfully.")  # Debug log
    except Exception as e:
        print(f"Error during database setup: {e}")
    finally:
        conn.close()

# Save playlist with metadata to database
def save_playlist_to_db():
    conn = sqlite3.connect("playlist.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM playlists")  # Clear old entries

    for file in playlist:
        tag = TinyTag.get(file)  # Extract metadata
        title = tag.title if tag.title else "Unknown Title"
        album = tag.album if tag.album else "Unknown Album"
        artist = tag.artist if tag.artist else "Unknown Artist"
        bitrate = tag.bitrate if tag.bitrate else None
        
        cursor.execute(
            """
            INSERT INTO playlists (file_path, title, album, artist, bitrate)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file, title, album, artist, bitrate)
        )
    conn.commit()
    conn.close()
    messagebox.showinfo("Playlist Saved", "Playlist has been saved to the database with metadata!")

# Load playlist with metadata from database
def load_playlist_from_db():
    global playlist
    conn = sqlite3.connect("playlist.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, title, album, artist FROM playlists")
    rows = cursor.fetchall()
    conn.close()

    playlist = [row[0] for row in rows]
    playlist_box.delete(0, tk.END)
    for row in rows:
        file_display = f"{row[1]} - {row[2]} ({row[3]})" if row[1] != "Unknown Title" else row[0].split('/')[-1]
        playlist_box.insert(tk.END, file_display)
    
    messagebox.showinfo("Playlist Loaded", "Playlist with metadata has been loaded from the database!")

# Load playlist with sorting
def load_sorted_playlist(sort_by):
    global playlist
    conn = sqlite3.connect("playlist.db")
    cursor = conn.cursor()

    # Sort by the selected column (title, album, artist)
    query = f"SELECT file_path, title, album, artist FROM playlists ORDER BY {sort_by} ASC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    # Clear and update playlist box
    playlist = [row[0] for row in rows]
    playlist_box.delete(0, tk.END)
    for row in rows:
        file_display = f"{row[1]} - {row[2]} ({row[3]})" if row[1] != "Unknown Title" else row[0].split('/')[-1]
        playlist_box.insert(tk.END, file_display)

    messagebox.showinfo("Playlist Sorted", f"Playlist has been sorted by {sort_by.capitalize()}!")


# Function to format time (milliseconds to mm:ss format)
def format_time(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

# Functions for visualizer
def draw_bars(canvas, bar_width, running_flag, bar_color="white"):
    canvas.delete("bars")
    width = canvas.winfo_width()
    height = canvas.winfo_height()

    if running_flag[0]:  # Only proceed if running
        for i in range(0, width, bar_width):
            bar_height = random.randint(int(height / 8), int(height / 2.5))
            canvas.create_line(i, height, i, height - bar_height, tags=("bars",), width=bar_width, fill=bar_color)
        canvas.after(50, lambda: draw_bars(canvas, bar_width, running_flag, bar_color))

def start_visualizer(canvas, bar_width, running_flag, bar_color):
    if not running_flag[0]:  # Prevent multiple instances
        running_flag[0] = True
        draw_bars(canvas, bar_width, running_flag, bar_color)

def stop_visualizer(running_flag):
    running_flag[0] = False

# Music player functions
def add_to_playlist():
    global playlist
    files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.ogg *.wav *.flac")])
    for file in files:
        playlist.append(file)
        playlist_box.insert(tk.END, file.split('/')[-1])

def play_song():
    global current_index
    selected_index = playlist_box.curselection()
    if selected_index:
        current_index = selected_index[0]
        start_playback()

def start_playback():
    global current_index
    if current_index is not None and 0 <= current_index < len(playlist):
        playlist_box.selection_clear(0, tk.END)
        playlist_box.selection_set(current_index)
        playlist_box.activate(current_index)

        file_path = playlist[current_index]
        media = instance.media_new(file_path)
        player.set_media(media)
        player.play()

        show_metadata(file_path)
        start_visualizer(canvas, bar_width=10, running_flag=running_flag, bar_color="cyan")
        update_time_labels()
        check_song_end()

def check_song_end():
    if player.get_state() == vlc.State.Ended:
        play_next()
    else:
        root.after(1000, check_song_end)

def pause_song():
    if player.is_playing():
        player.pause()
        stop_visualizer(running_flag)

def resume_song():
    if not player.is_playing():
        player.play()
        start_visualizer(canvas, bar_width=10, running_flag=running_flag, bar_color="cyan")
        update_time_labels()

def stop_song():
    player.stop()
    stop_visualizer(running_flag)

def play_next():
    global current_index
    if current_index is not None and current_index + 1 < len(playlist):
        current_index += 1
        start_playback()

def play_previous():
    global current_index
    if current_index is not None and current_index - 1 >= 0:
        current_index -= 1
        start_playback()

def update_time_labels():
    if player.is_playing():
        current_time = player.get_time()
        total_time = player.get_length()

        current_time_label.configure(text=f"Current Time: {format_time(current_time)}")
        total_time_label.configure(text=f"Total Time: {format_time(total_time)}")

        if total_time > 0:
            progress = current_time / total_time
            progress_bar.set(progress)
    else:
        current_time_label.configure(text="Current Time: 00:00:00")
        total_time_label.configure(text="Total Time: 00:00:00")
        progress_bar.set(0)
    
    root.after(500, update_time_labels)

def seek(event):
    if player.is_playing():
        total_time = player.get_length()
        if total_time > 0:
            progress_fraction = event.x / progress_bar.winfo_width()
            new_time = int(progress_fraction * total_time)
            player.set_time(new_time)
            update_time_labels()

def show_metadata(file_path):
    tag = TinyTag.get(file_path)
    title = tag.title if tag.title else "Unknown Title"
    album = tag.album if tag.album else "Unknown Album"
    artist = tag.artist if tag.artist else "Unknown Artist"
    bitrate = tag.bitrate if tag.bitrate else "Unknown Bitrate"
    metadata_label.configure(text=f"Title: {title}\nAlbum: {album}\nArtist: {artist}\nBitrate: {bitrate} kbps")

# Initialize Tkinter with CustomTkinter
root = ctk.CTk()
root.title("Music Player")
root.geometry("1350x550")
root.minsize(1350, 550)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

setup_database()  # Set up the database

# Playlist and buttons
plframe = ctk.CTkFrame(root, width=200, height=100)
plframe.grid(row=0, column=0, sticky="ns", rowspan=3)

sort_frame = ctk.CTkFrame(plframe, height=50)
sort_frame.pack(fill="x", pady=10)

sort_title_button = ctk.CTkButton(sort_frame, text="Sort by Title", command=lambda: load_sorted_playlist("title"))
sort_title_button.pack(side="left", padx=5)

sort_album_button = ctk.CTkButton(sort_frame, text="Sort by Album", command=lambda: load_sorted_playlist("album"))
sort_album_button.pack(side="left", padx=5)

sort_artist_button = ctk.CTkButton(sort_frame, text="Sort by Artist", command=lambda: load_sorted_playlist("artist"))
sort_artist_button.pack(side="left", padx=5)
playlist_box = tk.Listbox(plframe, selectmode=tk.SINGLE, width=50, height=10)
playlist_box.pack(fill="both", expand="true")
playlist_box.bind("<Double-1>", lambda event: play_song())

mdframe = ctk.CTkFrame(root, width=200, height=100)
mdframe.grid(row=0, column=1, sticky="nsew")

canvas = ctk.CTkCanvas(mdframe, width=400, height=200, bg="black")
canvas.pack(fill="both", expand="true")

tframe = ctk.CTkFrame(mdframe, width=200, height=100)
tframe.pack(fill="x")

metadata_label = ctk.CTkLabel(tframe, text="Metadata: No song loaded", wraplength=350)
metadata_label.pack(pady=10)

btnframe = ctk.CTkFrame(root, width=200, height=100)
btnframe.grid(row=1, column=1, sticky="new", rowspan=2)

vbbody = ctk.CTkFrame(btnframe, height=100)
vbbody.pack(anchor="center", fill="x")

bbody = ctk.CTkFrame(btnframe, height=100)
bbody.pack(anchor="center")

add_button = ctk.CTkButton(bbody, text="Add to Playlist", command=add_to_playlist)
add_button.pack(pady=5, side="left")

play_button = ctk.CTkButton(bbody, text="Play", command=play_song)
play_button.pack(pady=5, side="left")

pause_button = ctk.CTkButton(bbody, text="Pause/Resume", command=lambda: resume_song() if not player.is_playing() else pause_song())
pause_button.pack(pady=5, side="left")

stop_button = ctk.CTkButton(bbody, text="Stop", command=stop_song)
stop_button.pack(pady=5, side="left")

prev_button = ctk.CTkButton(bbody, text="Previous", command=play_previous)
prev_button.pack(pady=5, side="left")

next_button = ctk.CTkButton(bbody, text="Next", command=play_next)
next_button.pack(pady=5, side="left")

save_button = ctk.CTkButton(bbody, text="Save Playlist", command=save_playlist_to_db)
save_button.pack(pady=5, side="left")

load_button = ctk.CTkButton(bbody, text="Load Playlist", command=load_playlist_from_db)
load_button.pack(pady=5, side="left")

progress_bar = ctk.CTkProgressBar(vbbody, width=800)
progress_bar.pack(fill="x", pady=10)
progress_bar.bind("<Button-1>", seek)

current_time_label = ctk.CTkLabel(mdframe, text="Current Time: 00:00:00")
current_time_label.pack(pady=5, side="left")

total_time_label = ctk.CTkLabel(mdframe, text="Total Time: 00:00:00")
total_time_label.pack(pady=5, side="right")

root.mainloop()

