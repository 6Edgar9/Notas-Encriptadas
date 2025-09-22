# ci — Gestor de notas cifradas con AES-GCM y PBKDF2

**ci** es un pequeño gestor de notas cifradas para uso educativo que muestra un esquema seguro de cifrado:
- Derivación de clave con PBKDF2-HMAC-SHA256 (KDF).
- Cifrado autenticado con `AES-GCM` (AEAD) para confidencialidad e integridad.
- Persistencia en un único archivo JSON (`notes_data.json`) que almacena el salt, el test cifrado y las notas cifradas.

> ⚠️ Proyecto educativo: aunque el script sigue buenas prácticas (KDF y AEAD), revisa las recomendaciones de seguridad en la sección correspondiente antes de usarlo en producción.

## Características principales

- Creación, listado y edición de notas cifradas.
- Derivación de clave a partir de contraseña maestra usando PBKDF2.
- Uso de `AESGCM` para cifrado autenticado (nonce + ciphertext + tag).
- Archivo único `notes_data.json` que guarda salt (base64), el test cifrado y las notas encriptadas.

## Requisitos

- Python 3.8+
- Dependencias:
  ```bash
  pip install -r requirements.txt
  ```

## Instalación y uso

1. Clona el repositorio:
```bash
git clone https://github.com/6Edgar9/Notas-Encriptadas.git
cd ci
```

2. (Opcional) Crea y activa un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate    # Windows (cmd)
```

3. Instala dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta:
```bash
python ci.py
```

- La primera ejecución pedirá establecer una contraseña maestra.  
- El archivo `notes_data.json` almacenará el `salt` (base64), un `test` cifrado (para verificar la contraseña) y la lista `notes` con títulos y contenidos cifrados.

## Notas de seguridad y recomendaciones

- **Protege el archivo `notes_data.json`**. Ajusta permisos (`chmod 600`) y evita respaldos inseguros.
- **No reuses parámetros**: el salt debe ser aleatorio por cuenta/archivo (el script ya lo genera con `os.urandom(16)`).
- **Valida iteraciones de KDF**: 100.000 iteraciones es un valor razonable; ajústalo según el entorno y la amenaza (movimientos GPU).
- **Gestión de contraseñas**: no caches la contraseña en memoria más tiempo del necesario.
- **Backups y recuperación**: si pierdes la contraseña, los datos serán irrecuperables. Diseña un plan de recuperación si es necesario.
- **Auditoría**: añade logging limitado y pruebas unitarias para evitar errores.

## Posibles mejoras

- Añadir función de eliminación de notas.
- Añadir exportación/backup cifrado y opción de cambiar contraseña (rotación de claves).
- Integrar una interfaz gráfica o API con autenticación adicional.
- Añadir control de versiones en el esquema de cifrado (para migraciones futuras).
- Añadir pruebas automáticas (pytest) y validación del archivo JSON.

## Estructura sugerida del repositorio

```
ci/
├── ci.py                  # Script principal
├── requirements.txt
├── README.md
├── .gitignore
└── notes_data.json        # generado en tiempo de ejecución (ignorado)
```

---

#### Dios, Assembly y la Patria
#### Edrem

---

Desarrollado con fines académicos y de práctica en Python.