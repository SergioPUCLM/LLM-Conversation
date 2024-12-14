from pynput.keyboard import Key, Listener
import time

# Variables para controlar si la barra espaciadora está presionada y el tiempo de inicio
is_space_pressed = False
start_time = 0

def on_press(key):
    global is_space_pressed, start_time
    if key == Key.space and not is_space_pressed:  # Detecta si empieza a ser presionada
        is_space_pressed = True
        start_time = time.time()  # Registrar el tiempo de inicio
        print("La barra espaciadora está siendo presionada.")
        # while is_space_pressed:
        #     time.sleep(0.1)  # Esperar un poco antes de verificar nuevamente
    print("hola")
      

def on_release(key):
    global is_space_pressed, start_time
    if key == Key.space and is_space_pressed:  # Detecta si se deja de presionar
        is_space_pressed = False
        elapsed_time = time.time() - start_time  # Calcular el tiempo transcurrido
        print(f"La barra espaciadora fue presionada durante {elapsed_time:.2f} segundos.")
    if key == Key.esc:  # Salir del programa al presionar ESC
        print("Saliendo...") 
        return False

# Configurar el Listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
