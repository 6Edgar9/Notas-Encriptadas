import os
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import urlsafe_b64encode, urlsafe_b64decode
from getpass import getpass

# Archivo donde se guardarán las notas y la contraseña cifrada
DATA_FILE = "notes_data.json"
TEST_STRING = "verification"  # Texto de prueba para verificar la clave

# --- FUNCIONES CRIPTOGRÁFICAS ---

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_message(key: bytes, plaintext: str) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return urlsafe_b64encode(nonce + ciphertext).decode()

def decrypt_message(key: bytes, encrypted_text: str) -> str:
    data = urlsafe_b64decode(encrypted_text.encode())
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()

def generate_signature(key: bytes, data_to_sign: dict) -> str:
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    data_string = json.dumps(data_to_sign, sort_keys=True)
    h.update(data_string.encode())
    return urlsafe_b64encode(h.finalize()).decode()

# --- FUNCIONES DE MANEJO DE DATOS ---

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {"password": None, "notes": [], "test": None, "signature": None}

def save_secure_data(data, key):
    data_to_sign = {"test": data["test"], "notes": data["notes"]}
    data["signature"] = generate_signature(key, data_to_sign)
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- MENÚ PRINCIPAL ---

def main():
    data = load_data()
    
    if data.get("password") is None:
        clear_screen()
        print("\n=== CONFIGURACIÓN INICIAL ===")
        print("Establece una contraseña maestra:")
        password = getpass("Contraseña: ")
        
        salt = os.urandom(16)
        key = derive_key(password, salt)
        
        data["password"] = urlsafe_b64encode(salt).decode()
        data["test"] = encrypt_message(key, TEST_STRING)
        data["notes"] = []
        
        save_secure_data(data, key)
        print("\n✅ Contraseña maestra establecida correctamente.")
    else:
        clear_screen()
        print("\n=== INICIO DE SESIÓN ===")
        password = getpass("Ingresa la contraseña maestra: ")
        
        salt = urlsafe_b64decode(data["password"].encode())
        key = derive_key(password, salt)
        
        try:
            test_decrypted = decrypt_message(key, data["test"])
            if test_decrypted != TEST_STRING:
                raise ValueError("Clave incorrecta")
                
            data_to_verify = {"test": data.get("test"), "notes": data.get("notes", [])}
            expected_signature = generate_signature(key, data_to_verify)
            
            if data.get("signature") != expected_signature:
                clear_screen()
                print("\n🚨 ¡ALERTA DE SEGURIDAD! 🚨")
                print("El archivo de notas ha sido modificado, corrompido o manipulado externamente.")
                print("La firma de integridad no coincide.")
                input("\nPresiona Enter para salir...")
                return

            print("\n✅ Contraseña verificada.")
        except Exception:
            print("\n❌ Contraseña incorrecta o datos corruptos. Saliendo...")
            return

    while True:
        clear_screen()
        print("\n--- MENÚ PRINCIPAL ---")
        print("1. Crear nota")
        print("2. Listar notas")
        print("3. Editar nota")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ")

        if opcion == "1":
            clear_screen()
            print("\n--- CREAR NOTA ---")
            print("(Ingresa '0' en el título para cancelar y volver al menú)")
            
            titulo = input("\nEscribe el título: ")
            if titulo.strip() == '0':
                continue
                
            nota = input("Escribe el contenido: ")
            
            encrypted_title = encrypt_message(key, titulo)
            encrypted_note = encrypt_message(key, nota)
            data["notes"].append({"title": encrypted_title, "content": encrypted_note})
            
            save_secure_data(data, key)
            print("\n✅ Nota creada y cifrada correctamente.")
            input("\nPresiona Enter para continuar...")

        elif opcion == "2":
            clear_screen()
            print("\n--- TUS NOTAS ---")
            if not data["notes"]:
                print("No hay notas guardadas aún.")
                input("\nPresiona Enter para volver...")
                continue
            
            for i, note in enumerate(data["notes"], 1):
                decrypted_title = decrypt_message(key, note["title"])
                print(f"{i}. {decrypted_title}")
                
            num_nota = input("\nSelecciona el número de la nota para leerla (o '0' para salir): ")
            
            if num_nota == '0':
                continue
                
            if num_nota.isdigit():
                num_nota = int(num_nota) - 1
                if 0 <= num_nota < len(data["notes"]):
                    decrypted_note = decrypt_message(key, data["notes"][num_nota]["content"])
                    decrypted_title = decrypt_message(key, data["notes"][num_nota]["title"])
                    print(f"\n{'='*40}")
                    print(f"TÍTULO: {decrypted_title}")
                    print(f"{'='*40}")
                    print(f"{decrypted_note}")
                    print(f"{'='*40}")
                else:
                    print("\n❌ Número de nota inválido.")
            input("\nPresiona Enter para continuar...")

        elif opcion == "3":
            clear_screen()
            print("\n--- EDITAR NOTA ---")
            if not data["notes"]:
                print("No hay notas para editar.")
                input("\nPresiona Enter para volver...")
                continue
            
            for i, note in enumerate(data["notes"], 1):
                decrypted_title = decrypt_message(key, note["title"])
                print(f"{i}. {decrypted_title}")
                
            num_nota = input("\nSelecciona el número a editar (o '0' para salir): ")
            
            if num_nota == '0':
                continue
                
            if num_nota.isdigit():
                num_nota = int(num_nota) - 1
                if 0 <= num_nota < len(data["notes"]):
                    while True:
                        clear_screen()
                        decrypted_title = decrypt_message(key, data["notes"][num_nota]["title"])
                        print(f"\n=== EDITANDO: {decrypted_title} ===")
                        print("1. Editar Título")
                        print("2. Editar Contenido")
                        print("0. Volver al menú principal")
                        
                        sub_opcion = input("\nSelecciona qué deseas editar: ")
                        
                        if sub_opcion == "1":
                            print(f"\n[Título actual]: {decrypted_title}")
                            nuevo_titulo = input("Nuevo título (Enter para no cambiar): ")
                            if nuevo_titulo.strip():
                                data["notes"][num_nota]["title"] = encrypt_message(key, nuevo_titulo)
                                save_secure_data(data, key)
                                print("\n✅ Título actualizado y cifrado.")
                                input("Presiona Enter para continuar...")
                                
                        elif sub_opcion == "2":
                            decrypted_note = decrypt_message(key, data["notes"][num_nota]["content"])
                            print(f"\n[Contenido actual]:\n{decrypted_note}")
                            print("\n(Tip: Copia el texto de arriba, pégalo en la consola, edítalo y presiona Enter)")
                            nueva_nota = input("\nNuevo contenido (Enter para no cambiar): ")
                            if nueva_nota.strip():
                                data["notes"][num_nota]["content"] = encrypt_message(key, nueva_nota)
                                save_secure_data(data, key)
                                print("\n✅ Contenido actualizado y cifrado.")
                                input("Presiona Enter para continuar...")
                                
                        elif sub_opcion == "0":
                            break
                        else:
                            print("\n❌ Opción inválida.")
                            input("Presiona Enter para continuar...")
                else:
                    print("\n❌ Número de nota inválido.")
                    input("\nPresiona Enter para continuar...")

        elif opcion == "0":
            clear_screen()
            print("\nCerrando baúl de notas de forma segura... ¡Hasta luego!")
            break

        else:
            print("\n❌ Opción inválida. Intenta de nuevo.")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()