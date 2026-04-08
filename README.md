# PakayVault — Gestor de notas cifradas con AES-GCM, PBKDF2 y HMAC

**PakayVault** es un gestor de notas por consola seguro y estructurado. Utiliza un esquema de cifrado robusto para proteger tanto la confidencialidad de la información como la integridad global de los datos almacenados.

## ¿Por qué el nombre "PakayVault"?
El nombre es una fusión de dos mundos:
* **Pakay:** Proviene del idioma quechua (lengua originaria de los Andes peruanos) y significa *"esconder"*, *"ocultar"* o *"guardar en secreto"*.
* **Vault:** Del inglés, que significa *"bóveda"* o *"caja fuerte"*.

Juntos, **PakayVault** representa una fortaleza digital inexpugnable para tus secretos, rindiendo homenaje a la riqueza lingüística y cultural del Perú.

---

## Características principales

- **Cifrado Autenticado Individual:** Uso de `AES-GCM` (AEAD) para cifrar el título y el contenido de cada nota por separado, utilizando un nonce aleatorio de 12 bytes por operación.
- **Derivación de Clave Robusta:** Implementa `PBKDF2-HMAC-SHA256` con **600,000 iteraciones** y un *salt* dinámico, cumpliendo con los estándares actuales para mitigar ataques de fuerza bruta por hardware moderno (GPU/ASIC).
- **Protección de Integridad Global (HMAC):** Todo el archivo `notes_data.json` está sellado con una firma HMAC. Si un atacante intenta alterar, borrar o intercambiar notas manualmente en el archivo, el sistema detectará la corrupción y bloqueará el acceso.
- **Gestión Intuitiva:** Creación, listado y edición independiente (título o contenido) de notas directamente desde la consola, sin exponer el texto plano en disco.

## Requisitos

- Python 3.8+
- Dependencias:
  ```bash
  pip install cryptography
  ```

## Instalación y uso

1. Clona el repositorio:
```bash
git clone [https://github.com/tu-usuario/PakayVault.git](https://github.com/tu-usuario/PakayVault.git)
cd PakayVault
```

2. (Opcional) Crea y activa un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows (cmd)
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta el programa:
```bash
python ci.py
```

### Primer inicio de sesión
La primera ejecución te pedirá establecer una contraseña maestra. A partir de esa contraseña, el sistema generará el archivo `notes_data.json`, el cual almacenará:
- El `salt` (en base64).
- Un texto de prueba cifrado (`test`) para validar tu contraseña en futuros inicios de sesión.
- Tus `notes` (títulos y contenidos cifrados).
- La firma global de integridad (`signature`).

> **⚠️ Advertencia:** Si pierdes tu contraseña maestra, los datos serán **matemáticamente irrecuperables**. PakayVault no posee "puertas traseras" (backdoors) ni mecanismos de recuperación por diseño.

## Notas de seguridad y recomendaciones

- **Protege el archivo `notes_data.json`:** Ajusta los permisos del sistema operativo (ej. `chmod 600` en sistemas Unix) para que solo tu usuario pueda leerlo.
- **Iteraciones de PBKDF2:** El valor actual es de 600,000 iteraciones. Esto hace que generar la llave tarde una fracción de segundo, pero hace inviable la adivinación automatizada.
- **Evita keyloggers:** Al ser una herramienta de consola, asegúrate de ejecutarla en un entorno libre de malware que pueda capturar las pulsaciones de tu teclado.

## Estructura del proyecto

```text
PakayVault/
├── ci.py                  # Script principal y lógica criptográfica
├── requirements.txt       # Dependencias del proyecto
├── README.md              # Documentación
├── .gitignore             
└── notes_data.json        # Generado en tiempo de ejecución (¡No subir al repo!)
```

---

#### Dios, Assembly y la Patria
#### Edrem

---
*Desarrollado con fines académicos y aplicación de buenas prácticas en criptografía con Python.*