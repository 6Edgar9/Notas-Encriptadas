import os
import json
import tempfile
import subprocess
import gc
from base64 import urlsafe_b64encode, urlsafe_b64decode
from getpass import getpass

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DATA_FILE = "notes_data.json"
TEST_STRING = "verification"

class CryptoManager:
    """Clase estática para aislar las operaciones criptográficas delicadas."""
    @staticmethod
    def derive_keys(password: str, salt: bytes) -> tuple:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=64,
            salt=salt,
            iterations=600000,
            backend=default_backend()
        )
        master_key = kdf.derive(password.encode())
        return master_key[:32], master_key[32:]

    @staticmethod
    def encrypt(key: bytes, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return urlsafe_b64encode(nonce + ciphertext).decode()

    @staticmethod
    def decrypt(key: bytes, encrypted_text: str) -> str:
        data = urlsafe_b64decode(encrypted_text.encode())
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

    @staticmethod
    def generate_signature(mac_key: bytes, data_to_sign: dict) -> str:
        h = hmac.HMAC(mac_key, hashes.SHA256(), backend=default_backend())
        data_string = json.dumps(data_to_sign, sort_keys=True, separators=(',', ':'))
        h.update(data_string.encode())
        return urlsafe_b64encode(h.finalize()).decode()

class VaultManager:
    """Maneja el estado y persistencia de la bóveda."""
    def __init__(self):
        self.data = {"password": None, "notes": [], "test": None, "signature": None}
        self.enc_key = None
        self.mac_key = None
        self.salt = None
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                self.data = json.load(file)

    def save_data(self):
        data_to_sign = {"test": self.data["test"], "notes": self.data["notes"]}
        self.data["signature"] = CryptoManager.generate_signature(self.mac_key, data_to_sign)
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)

    def is_configured(self) -> bool:
        return self.data.get("password") is not None

    def initialize_vault(self, password: str):
        self.salt = os.urandom(16)
        self.enc_key, self.mac_key = CryptoManager.derive_keys(password, self.salt)
        
        self.data["password"] = urlsafe_b64encode(self.salt).decode()
        self.data["test"] = CryptoManager.encrypt(self.enc_key, TEST_STRING)
        self.data["notes"] = []
        self.save_data()

    def unlock_vault(self, password: str) -> bool:
        try:
            self.salt = urlsafe_b64decode(self.data["password"].encode())
            test_enc_key, test_mac_key = CryptoManager.derive_keys(password, self.salt)
            
            test_decrypted = CryptoManager.decrypt(test_enc_key, self.data["test"])
            if test_decrypted != TEST_STRING:
                return False
                
            data_to_verify = {"test": self.data.get("test"), "notes": self.data.get("notes", [])}
            expected_signature = CryptoManager.generate_signature(test_mac_key, data_to_verify)
            
            if self.data.get("signature") != expected_signature:
                raise ValueError("HMAC_FAIL")
                
            self.enc_key = test_enc_key
            self.mac_key = test_mac_key
            return True
        except ValueError as ve:
            if str(ve) == "HMAC_FAIL":
                raise ve
            return False
        except Exception:
            return False

    def change_password(self, new_password: str):
        new_salt = os.urandom(16)
        new_enc_key, new_mac_key = CryptoManager.derive_keys(new_password, new_salt)
        
        new_notes = []
        for note in self.data["notes"]:
            dec_title = CryptoManager.decrypt(self.enc_key, note["title"])
            dec_content = CryptoManager.decrypt(self.enc_key, note["content"])
            
            new_notes.append({
                "title": CryptoManager.encrypt(new_enc_key, dec_title),
                "content": CryptoManager.encrypt(new_enc_key, dec_content)
            })
            
        self.data["password"] = urlsafe_b64encode(new_salt).decode()
        self.data["test"] = CryptoManager.encrypt(new_enc_key, TEST_STRING)
        self.data["notes"] = new_notes
        
        self.enc_key = new_enc_key
        self.mac_key = new_mac_key
        self.salt = new_salt
        self.save_data()

    def add_note(self, title: str, content: str):
        encrypted_title = CryptoManager.encrypt(self.enc_key, title)
        encrypted_note = CryptoManager.encrypt(self.enc_key, content)
        self.data["notes"].append({"title": encrypted_title, "content": encrypted_note})
        self.save_data()

    def get_notes_count(self) -> int:
        return len(self.data["notes"])

    def get_decrypted_title(self, index: int) -> str:
        return CryptoManager.decrypt(self.enc_key, self.data["notes"][index]["title"])

    def get_decrypted_content(self, index: int) -> str:
        return CryptoManager.decrypt(self.enc_key, self.data["notes"][index]["content"])

    def update_note(self, index: int, new_title: str = None, new_content: str = None):
        if new_title is not None:
            self.data["notes"][index]["title"] = CryptoManager.encrypt(self.enc_key, new_title)
        if new_content is not None:
            self.data["notes"][index]["content"] = CryptoManager.encrypt(self.enc_key, new_content)
        self.save_data()

    def delete_note(self, index: int):
        del self.data["notes"][index]
        self.save_data()

class PakayCLI:
    """Maneja la interacción de consola, liberando a la bóveda de la lógica I/O."""
    def __init__(self):
        self.vault = VaultManager()

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def secure_delete_file(filepath: str, passes=3):
        """Sobrescribe el archivo temporal con basura aleatoria antes de borrarlo (Shredding)."""
        if not os.path.exists(filepath):
            return
        try:
            length = os.path.getsize(filepath)
            with open(filepath, "br+") as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(length))
            os.unlink(filepath)
        except Exception:
            pass # Falla silenciosa si no se puede borrar, usualmente por bloqueos del SO

    def edit_in_editor(self, initial_content="") -> str:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding='utf-8') as temp_file:
            temp_file.write(initial_content)
            temp_file_name = temp_file.name
        
        editor = os.environ.get('EDITOR', 'notepad' if os.name == 'nt' else 'nano')
        edited_content = ""
        try:
            subprocess.call([editor, temp_file_name])
            with open(temp_file_name, 'r', encoding='utf-8') as file_read:
                edited_content = file_read.read()
        finally:
            self.secure_delete_file(temp_file_name)
                
        return edited_content

    def run(self):
        if not self.vault.is_configured():
            self.setup_vault()
        else:
            if not self.login():
                return
        self.main_menu()

    def setup_vault(self):
        self.clear_screen()
        print("\n=== CONFIGURACIÓN INICIAL ===")
        print("Establece una contraseña maestra:")
        while True:
            password = getpass("Contraseña: ")
            confirm = getpass("Confirma la contraseña: ")
            if password == confirm:
                break
            print("❌ Las contraseñas no coinciden. Inténtalo de nuevo.\n")
        
        self.vault.initialize_vault(password)
        print("\n✅ Contraseña maestra establecida correctamente.")

    def login(self) -> bool:
        self.clear_screen()
        print("\n=== INICIO DE SESIÓN ===")
        password = getpass("Ingresa la contraseña maestra: ")
        
        try:
            if self.vault.unlock_vault(password):
                print("\n✅ Contraseña verificada.")
                return True
            else:
                print("\n❌ Contraseña incorrecta o datos corruptos. Saliendo...")
                return False
        except ValueError as e:
            if str(e) == "HMAC_FAIL":
                self.clear_screen()
                print("\n🚨 ¡ALERTA DE SEGURIDAD! 🚨")
                print("El archivo de notas ha sido modificado, corrompido o manipulado externamente.")
                print("La firma de integridad no coincide.")
                input("\nPresiona Enter para salir...")
            return False

    def select_note(self, action_name: str) -> int:
        """Helper para listar y seleccionar una nota."""
        if self.vault.get_notes_count() == 0:
            print("No hay notas disponibles.")
            return -1
            
        for i in range(self.vault.get_notes_count()):
            print(f"{i + 1}. {self.vault.get_decrypted_title(i)}")
            
        num_nota = input(f"\nSelecciona el número de la nota para {action_name} (o '0' para cancelar): ")
        if num_nota.isdigit():
            idx = int(num_nota) - 1
            if 0 <= idx < self.vault.get_notes_count():
                return idx
        print("\n❌ Selección inválida o cancelada.")
        return -1

    def create_note(self):
        self.clear_screen()
        print("\n--- CREAR NOTA ---")
        titulo = input("\nEscribe el título (o '0' para cancelar): ")
        if titulo.strip() == '0':
            return
            
        print("\nSe abrirá el editor de texto para que escribas el contenido de tu nota.")
        input("Presiona Enter para abrir el editor...")
        nota = self.edit_in_editor()
        
        if not nota.strip():
            print("\n❌ La nota está vacía. Cancelando creación.")
        else:
            self.vault.add_note(titulo, nota)
            print("\n✅ Nota creada y cifrada correctamente.")
        input("Presiona Enter para continuar...")

    def read_note(self):
        self.clear_screen()
        print("\n--- TUS NOTAS ---")
        idx = self.select_note("leerla")
        if idx != -1:
            title = self.vault.get_decrypted_title(idx)
            content = self.vault.get_decrypted_content(idx)
            print(f"\n{'='*40}")
            print(f"TÍTULO: {title}")
            print(f"{'='*40}")
            print(content)
            print(f"{'='*40}")
            input("\nPresiona Enter para continuar...")

    def edit_note(self):
        self.clear_screen()
        print("\n--- EDITAR NOTA ---")
        idx = self.select_note("editar")
        if idx != -1:
            while True:
                self.clear_screen()
                title = self.vault.get_decrypted_title(idx)
                print(f"\n=== EDITANDO: {title} ===")
                print("1. Editar Título")
                print("2. Editar Contenido")
                print("0. Volver al menú principal")
                
                sub_opcion = input("\nSelecciona qué deseas editar: ")
                if sub_opcion == "1":
                    nuevo_titulo = input(f"Nuevo título (Actual: {title}): ")
                    if nuevo_titulo.strip():
                        self.vault.update_note(idx, new_title=nuevo_titulo)
                        print("\n✅ Título actualizado y cifrado.")
                        input("Presiona Enter para continuar...")
                elif sub_opcion == "2":
                    content = self.vault.get_decrypted_content(idx)
                    print("\nAbriendo el editor con el contenido actual...")
                    input("Presiona Enter para abrir el editor...")
                    nueva_nota = self.edit_in_editor(content)
                    if nueva_nota.strip() and nueva_nota != content:
                        self.vault.update_note(idx, new_content=nueva_nota)
                        print("\n✅ Contenido actualizado y cifrado.")
                    elif not nueva_nota.strip():
                        print("\n❌ La nota no puede estar vacía. No se guardaron los cambios.")
                    else:
                        print("\nℹ️ No se hicieron cambios.")
                    input("Presiona Enter para continuar...")
                elif sub_opcion == "0":
                    break

    def delete_note_ui(self):
        self.clear_screen()
        print("\n--- BORRAR NOTA ---")
        idx = self.select_note("borrar")
        if idx != -1:
            title = self.vault.get_decrypted_title(idx)
            confirm = input(f"¿Estás seguro de que deseas borrar '{title}'? (s/n): ")
            if confirm.lower() == 's':
                self.vault.delete_note(idx)
                print("\n✅ Nota borrada correctamente.")
            else:
                print("\n❌ Operación cancelada.")
            input("Presiona Enter para continuar...")

    def change_password_ui(self):
        self.clear_screen()
        print("\n--- CAMBIAR CONTRASEÑA MAESTRA ---")
        old_password = getpass("Ingresa tu contraseña actual: ")
        
        try:
            test_enc, _ = CryptoManager.derive_keys(old_password, self.vault.salt)
            if CryptoManager.decrypt(test_enc, self.vault.data["test"]) != TEST_STRING:
                raise ValueError
        except:
            print("\n❌ Contraseña actual incorrecta.")
            input("Presiona Enter para volver...")
            return
            
        print("\nEstablece tu NUEVA contraseña maestra:")
        while True:
            new_password = getpass("Nueva contraseña: ")
            new_confirm = getpass("Confirma nueva contraseña: ")
            if new_password == new_confirm:
                break
            print("❌ Las contraseñas no coinciden. Inténtalo de nuevo.\n")
            
        self.vault.change_password(new_password)
        print("\n✅ Contraseña maestra cambiada exitosamente. Todas las notas han sido recifradas.")
        input("Presiona Enter para continuar...")

    def export_notes(self):
        self.clear_screen()
        print("\n--- EXPORTAR NOTAS A TEXTO PLANO ---")
        print("⚠️ ADVERTENCIA: Esta acción guardará todas tus notas en un archivo sin cifrar.")
        print("Cualquier persona con acceso a esta computadora podrá leerlas.")
        confirm = input("¿Estás seguro de que deseas continuar? (s/n): ")
        
        if confirm.lower() == 's':
            if self.vault.get_notes_count() == 0:
                print("\nNo hay notas para exportar.")
            else:
                export_file = "notas_exportadas.txt"
                try:
                    with open(export_file, "w", encoding="utf-8") as f:
                        f.write("=== PAKAYVAULT EXPORT ===\n\n")
                        for i in range(self.vault.get_notes_count()):
                            title = self.vault.get_decrypted_title(i)
                            content = self.vault.get_decrypted_content(i)
                            f.write(f"NOTA #{i+1}: {title}\n")
                            f.write("-" * 40 + "\n")
                            f.write(content + "\n")
                            f.write("=" * 40 + "\n\n")
                    print(f"\n✅ Notas exportadas exitosamente a '{export_file}'.")
                except Exception as e:
                    print(f"\n❌ Error al exportar las notas: {e}")
        else:
            print("\n❌ Operación cancelada.")
        input("\nPresiona Enter para continuar...")

    def main_menu(self):
        while True:
            self.clear_screen()
            print("\n--- MENÚ PRINCIPAL ---")
            print("1. Crear nota")
            print("2. Listar notas")
            print("3. Editar nota")
            print("4. Borrar nota")
            print("5. Cambiar contraseña maestra")
            print("6. Exportar notas a texto plano")
            print("0. Salir")
            opcion = input("\nSelecciona una opción: ")

            if opcion == "1":
                self.create_note()
            elif opcion == "2":
                self.read_note()
            elif opcion == "3":
                self.edit_note()
            elif opcion == "4":
                self.delete_note_ui()
            elif opcion == "5":
                self.change_password_ui()
            elif opcion == "6":
                self.export_notes()
            elif opcion == "0":
                self.clear_screen()
                print("\nCerrando baúl de notas de forma segura... ¡Hasta luego!")
                
                # Zeroing en medida de lo posible
                self.vault.enc_key = None
                self.vault.mac_key = None
                self.vault.salt = None
                gc.collect()
                break
            else:
                print("\n❌ Opción inválida. Intenta de nuevo.")
                input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    app = PakayCLI()
    app.run()