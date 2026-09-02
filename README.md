# ENTRENARIA

Pantalla para **entrenar el mostrador**: cargás fichas (a mano o Excel) y probás el chat. La IA no inventa piezas: solo lee lo que está en la base.

Esto **no es** el bot de WhatsApp (IAHAFID). Es un proyecto aparte, para usarlo en la PC del local.

## En la PC

1. Python 3.11 o más nuevo.
2. Clonar este repo y abrir **esta carpeta** en Cursor.
3. Entorno e instalación:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

4. Copiar `.env.example` a `.env` y poner la clave de Gemini en `OPENAI_API_KEY`. No subas `.env`.
5. Arrancar:

```powershell
.\arrancar.ps1
```

6. Abrir **http://127.0.0.1:8010**

## Cómo se entrena

No se entrena el modelo charlando. Se cargan **fichas**:

- Formulario a la izquierda, o
- Excel (una fila = una pieza; el mismo auto+conjunto se agrupa en una ficha).

Si el cliente pide una sola pieza, el chat ofrece el resto del conjunto y la marca que ustedes escribieron (Sachs, etc.). Si no está en la ficha, no lo inventa.

## Cursor

Abrí solo esta carpeta. Las reglas del repo piden que el asistente trabaje únicamente en ENTRENARIA.
