# PakayVault — Bóveda de Notas Cifradas 🛡️

**PakayVault** es un gestor de notas por consola extremadamente seguro, diseñado con Arquitectura Orientada a Objetos (POO) y estándares criptográficos de grado corporativo. Utiliza un esquema de cifrado robusto para proteger tanto la confidencialidad de tu información como la integridad global de los datos, evitando manipulaciones o análisis forenses básicos.

## ¿Por qué "PakayVault"?
El nombre es una fusión de dos mundos:
* **Pakay:** Del quechua, que significa *"esconder"*, *"ocultar"* o *"guardar en secreto"*.
* **Vault:** Del inglés, que significa *"bóveda"* o *"caja fuerte"*.

Juntos representan una fortaleza digital inexpugnable para tus secretos.

---

## 🔥 Características de Seguridad Avanzadas

1. **Cifrado Autenticado Individual (AES-256-GCM):** Cada nota y su título se cifran de forma independiente con nonces aleatorios de 12 bytes.
2. **Derivación de Llaves Independientes (PBKDF2-HMAC-SHA256):** A diferencia de gestores comunes, la bóveda usa **600,000 iteraciones** para generar 64 bytes de clave, separando matemáticamente la llave de cifrado (`enc_key`) de la llave de firma (`mac_key`).
3. **Protección Anti-Manipulación (Global HMAC):** Todo el archivo `notes_data.json` está sellado. Si un atacante intenta alterar, borrar un byte, o intercambiar el orden de tus notas en disco, el sistema detecta la corrupción y bloquea el acceso en defensa.
4. **File Shredding (Borrado de Grado Militar):** Para editar notas largas, el sistema abrirá un archivo de texto en tu editor por defecto (Ej. Bloc de Notas). Al guardarlo, PakayVault sobrescribirá la memoria temporal **3 veces con basura aleatoria criptográfica** (`os.urandom`) antes de eliminar el archivo, bloqueando recuperación por informática forense.
5. **Limpieza Activa de RAM:** Tras cerrar sesión, se gatilla el _Garbage Collector_ de Python explícitamente para vaciar las llaves simétricas de la memoria RAM.

---

## 🚀 Instalación y Uso (Desarrolladores)

1. **Clona y prepara el entorno:**
   ```bash
   git clone https://github.com/6Edgar9/Notas-Encriptadas
   cd PakayVault
   python -m venv venv
   # Activa tu entorno virtual dependiendo de tu SO (ej. venv\Scripts\activate)
   pip install -r requirements.txt
   ```

2. **Ejecuta la bóveda:**
   ```bash
   python pakayvault.py
   ```

---

## 📦 Compilación (Para usuarios sin Python)

Si deseas llevar la aplicación en una memoria USB o compartirla, puedes compilarla para obtener un ejecutable único y portable.

1. Simplemente haz doble clic en el archivo **`build.bat`**.
2. El script instalará `PyInstaller` y generará un archivo independiente.
3. Encuentra tu **`PakayVault.exe`** dentro de la carpeta `dist/`.

---

## 🛠️ Estructura del Proyecto

```text
PakayVault/
├── pakayvault.py          # Script principal (Arquitectura POO)
├── build.bat              # Automatizador de compilación para Windows
├── requirements.txt       # Dependencias del proyecto
├── README.md              # Documentación principal
├── .gitignore             # Archivos a ignorar por git
└── dist/                  # (Generado) Contiene el ejecutable compilado
    └── PakayVault.exe
```

> **⚠️ Advertencia:** Si pierdes tu contraseña maestra, los datos serán **matemáticamente irrecuperables**. PakayVault no posee mecanismos de recuperación de clave por diseño.

---
#### Dios, Assembly y la Patria
#### Edrem
*Desarrollado con fines académicos y aplicación de buenas prácticas en criptografía con Python.*