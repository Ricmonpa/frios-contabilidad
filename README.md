# N3Labs | Agente Contable Frios — Conciliador Mágico

Demo de conciliación automática **SAT (Dsoft) vs SAP Business One** y generación
del **Anexo 11 - IVA Acreditable (DIOT)**, con chat contable en lenguaje natural.

## Qué hace

1. **Integración de Datos** — sube el export de CFDIs de Dsoft (CSV/XLSX/XLSB;
   acepta el Anexo 11 tal como lo genera Dsoft) y simula la extracción de
   movimientos de SAP Business One.
2. **Conciliación Inteligente** — cruza SAT vs SAP por UUID, detecta facturas
   faltantes y diferencias de montos, y genera la pre-visualización del Anexo 11
   consolidada por proveedor (descargable en CSV).
3. **Chat Contable** — responde preguntas sobre la conciliación. Funciona con
   reglas sin costo; si se configura `GEMINI_API_KEY`, usa la API de Gemini.

## Correr en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud

1. Sube este repo a GitHub (puede ser privado).
2. Entra a [share.streamlit.io](https://share.streamlit.io), conecta tu cuenta
   de GitHub y elige este repo con `app.py` como archivo principal.
3. (Opcional, para el chat con LLM) En **App → Settings → Secrets** pega el
   contenido de `.streamlit/secrets.toml.example` con la clave real de Gemini.
4. (Recomendado para demos con clientes) En **Settings → Sharing** restringe el
   acceso a los correos invitados.

Cada `git push` a la rama principal redespliega la app automáticamente.

## Claves de API

- Nunca escribas claves en el código ni las subas a GitHub.
- En local viven en `.streamlit/secrets.toml` (ignorado por git).
- En la nube viven en el panel de Secrets de Streamlit Cloud.
- Sin clave, el chat cae automáticamente al modo de reglas: la demo completa
  funciona igual.

---

© 2025 N3Labs · Demo confidencial para Frios
