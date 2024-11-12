import os
import random
import time
import threading
from flask import Flask, render_template, jsonify
import pygame
import sys
import logging

# Inicializar Pygame mixer
pygame.mixer.init()

# Obtener la ruta base del archivo actual
base_path = os.path.dirname(os.path.abspath(__file__))

# Configuración de archivos
espera_audio = os.path.join(base_path, "sounds", "Espera.mp3")
silvato_inicio_audio = os.path.join(base_path, "sounds", "silvato_inicio.wav")
silvato_final_audio = os.path.join(base_path, "sounds", "silvato_final.wav")
music_folder = os.path.join(base_path, "Music")

# Duración de prueba (en minutos)
test_duration_minutes = 6  # Cambia a 10 para la duración real o cualquier valor que quieras probar

app = Flask(__name__)

# Estado global del juego
game_state = "espera"  # Puede ser "espera", "en_juego" o "terminado"
game_thread = None  # Hilo para la secuencia de música

# Configurar para evitar que Flask imprima logs en consola
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

# Funciones para imprimir mensajes en consola
def print_welcome_message():
    print("=" * 50)
    print("🎮 ¡Bienvenido al Juego de Rally de Confirma! 🎶")
    print("                Alexander Ubeda")
    print("=" * 50)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_welcome_message()

def show_countdown(duration_seconds):
    while duration_seconds > 0 and game_state == "en_juego":
        mins, secs = divmod(duration_seconds, 60)
        print(f"⏳ Tiempo restante: {mins:02d}:{secs:02d}", end="\r")
        time.sleep(1)
        duration_seconds -= 1
    print("\n")

# Funciones para reproducir y detener audio
def play_audio(file, volume=1.0):
    pygame.mixer.music.load(file)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()

def stop_audio():
    pygame.mixer.music.stop()

def play_music_sequence(duration_minutes):
    songs = [os.path.join(music_folder, song) for song in os.listdir(music_folder) if song.endswith(".wav")]
    played_songs = set()
    start_time = time.time()
    duration_seconds = duration_minutes * 60

    countdown_thread = threading.Thread(target=show_countdown, args=(duration_seconds,))
    countdown_thread.start()

    while time.time() - start_time < duration_seconds and game_state == "en_juego":
        available_songs = list(set(songs) - played_songs)
        if not available_songs:
            played_songs.clear()
            available_songs = songs
        
        song = random.choice(available_songs)
        played_songs.add(song)

        play_audio(song)
        while pygame.mixer.music.get_busy() and (time.time() - start_time < duration_seconds) and game_state == "en_juego":
            time.sleep(1)

    if game_state != "terminado":
        end_game_audio()

def end_game_audio():
    stop_audio()
    play_audio(silvato_final_audio)
    time.sleep(3)
    play_audio(espera_audio, volume=0.5)
    global game_state
    game_state = "espera"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/play_waiting")
def play_waiting():
    global game_state
    if game_state != "en_juego":
        stop_audio()
        play_audio(espera_audio, volume=0.5)
        game_state = "espera"
        clear_console()
        print("          🎵 El juego está en espera 🎵")
        return jsonify({"status": "En Espera"})
    else:
        return jsonify({"status": "El juego está en curso, no se puede poner en espera ahora."})

@app.route("/start_game")
def start_game():
    global game_state, game_thread
    if game_state == "espera":
        stop_audio()
        play_audio(silvato_inicio_audio)
        time.sleep(0.5)

        clear_console()
        
        print("          🏁 ¡El juego ha comenzado! 🏁\n")
        game_state = "en_juego"
        game_thread = threading.Thread(target=play_music_sequence, args=(test_duration_minutes,))
        game_thread.start()
        return jsonify({"status": "En Juego"})
    else:
        return jsonify({"status": "Ya está en juego o terminado"})

@app.route("/end_game")
def end_game():
    global game_state, game_thread
    if game_state == "en_juego":
        game_state = "terminado"
        if game_thread is not None:
            game_thread.join()
        threading.Thread(target=end_game_audio).start()
        clear_console()
        
        print("           🚩 El juego ha terminado 🚩\n")
        return jsonify({"status": "Juego Terminado"})
    else:
        return jsonify({"status": "El juego no está en curso"})

if __name__ == "__main__":
    print_welcome_message()
    app.run(host="0.0.0.0", port=5000, debug=True)
