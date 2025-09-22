import os
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import urlsafe_b64encode, urlsafe_b64decode
from getpass import getpass

# Archivo donde se guardarán las notas y la contraseña cifrada
DATA_FILE = "notes_data.json"
TEST_STRING = "verification"  # Texto de prueba para verificar la clave

# Función para derivar una clave a partir de una contraseña
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# Función para cifrar un texto con AES-256
def encrypt_message(key: bytes, plaintext: str) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return urlsafe_b64encode(nonce + ciphertext).decode()

# Función para descifrar un texto cifrado con AES-256
def decrypt_message(key: bytes, encrypted_text: str) -> str:
    data = urlsafe_b64decode(encrypted_text.encode())
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()

# Función para cargar las notas desde un archivo
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {"password": None, "notes": [], "test": None}

# Función para guardar las notas en un archivo
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Función para limpiar la pantalla
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Menú principal del programa
def main():
    data = load_data()
    if data["password"] is None:
        clear_screen()
        print("\nEstablece una contraseña maestra:")
        password = getpass("Contraseña: ")
        salt = os.urandom(16)
        key = derive_key(password, salt)
        data["password"] = urlsafe_b64encode(salt).decode()
        data["test"] = encrypt_message(key, TEST_STRING)
        save_data(data)
        print("\nContraseña maestra establecida correctamente.")
    else:
        clear_screen()
        password = getpass("\nIngresa la contraseña maestra: ")
        salt = urlsafe_b64decode(data["password"].encode())
        key = derive_key(password, salt)
        try:
            test_decrypted = decrypt_message(key, data["test"])
            if test_decrypted != TEST_STRING:
                raise ValueError("\nContraseña incorrecta.")
            print("\nContraseña verificada correctamente.")
        except Exception:
            print("\nContraseña incorrecta. Saliendo del programa...")
            return

    while True:
        clear_screen()
        print("\n--- MENÚ ---")
        print("0. Crear nota")
        print("1. Listar notas")
        print("2. Editar nota")
        print("3. Salir")
        opcion = input("\nSelecciona una opción: ")

        if opcion == "0":
            clear_screen()
            titulo = input("\nEscribe el título de la nota: ")
            nota = input("\nEscribe el contenido de la nota: ")
            encrypted_title = encrypt_message(key, titulo)
            encrypted_note = encrypt_message(key, nota)
            data["notes"].append({"title": encrypted_title, "content": encrypted_note})
            save_data(data)
            print("\nNota creada y cifrada correctamente.")
            input("\nPresiona Enter para continuar...")

        elif opcion == "1":
            clear_screen()
            print("\n--- LISTA DE NOTAS ---")
            for i, note in enumerate(data["notes"], 1):
                decrypted_title = decrypt_message(key, note["title"])
                print(f"{i}. {decrypted_title}")
            num_nota = int(input("\nSelecciona el número de la nota para ver el contenido: ")) - 1
            if 0 <= num_nota < len(data["notes"]):
                decrypted_note = decrypt_message(key, data["notes"][num_nota]["content"])
                print(f"\nContenido de la nota: {decrypted_note}")
            else:
                print("\nNúmero de nota inválido.")
            input("\nPresiona Enter para continuar...")

        elif opcion == "2":
            clear_screen()
            print("\n--- EDITAR NOTA ---")
            for i, note in enumerate(data["notes"], 1):
                decrypted_title = decrypt_message(key, note["title"])
                print(f"{i}. {decrypted_title}")
            num_nota = int(input("\nSelecciona el número de la nota a editar: ")) - 1
            if 0 <= num_nota < len(data["notes"]):
                nuevo_titulo = input("\nEscribe el nuevo título de la nota: ")
                nueva_nota = input("\nEscribe el nuevo contenido de la nota: ")
                data["notes"][num_nota]["title"] = encrypt_message(key, nuevo_titulo)
                data["notes"][num_nota]["content"] = encrypt_message(key, nueva_nota)
                save_data(data)
                print("\nNota editada y cifrada correctamente.")
            else:
                print("\nNúmero de nota inválido.")
            input("\nPresiona Enter para continuar...")

        elif opcion == "3":
            clear_screen()
            print("\nSaliendo del programa...")
            break

        else:
            print("\nOpción inválida. Intenta de nuevo.")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
