# Actualización: diez videos con locución sintética

La generación y montaje de voces ya no dependen de archivos ni herramientas del PC, de una API pagada ni de una clave del usuario. Se produjeron 60 locuciones por escena y diez pistas completas, y se integraron en los diez MP4 nuevos de `../renders_con_voz/`. Se conservan los originales y las diez pruebas anteriores sin voz.

## Voz y derechos documentados

Se utilizó Kokoro-82M v1.0, voz de catálogo `ef_dora`, con fonemización `es-419`. No se clonó a una persona ni se utilizó la voz del usuario. El proyecto oficial describe los pesos con licencia Apache 2.0, compatible con uso comercial; el runtime kokoro-onnx tiene licencia MIT. Se archivaron README, licencias, URLs, versiones y SHA256 observados de los modelos. Esto documenta el motor/modelo usado; no certifica aprobación corporativa del anuncio ni derechos sobre logos o stock ajenos.

`es-419` es un selector de fonemización para español latinoamericano, no una certificación de acento chileno. La naturalidad, pronunciación de Bupa, IntegraMédica, Isapre, Fonasa, Pymes y WhatsApp, y la adecuación a la marca requieren escucha humana. No se presenta esta locución como grabación de un locutor humano.

## Edición y mezcla realizadas

- Sesenta frases completas sintetizadas a velocidad 1,0 o hasta 1,05; no se cortaron palabras para encajarlas.
- Seis frases excedían el presupuesto inicial. Se ajustaron once fronteras de escena, tomando décimas de las pausas disponibles; no cambian las duraciones totales ni los cierres de cinco segundos. El JSON de secuencias registra antes/después y motivo. Estos ajustes editoriales se adoptaron dentro de la autorización del usuario para resolver y mejorar el montaje.
- Subtítulos ASS/SRT regenerados desde los tiempos fonéticos del propio modelo. Se verificó el mapeo de las sesenta frases y se agruparon correctamente las marcas que el fonemizador divide en dos. No son tiempos repartidos uniformemente ni una sincronía humana certificada.
- Voz centrada en estéreo. Música al menos 21 dB por debajo del RMS de voz en cada bloque, con otros 3 dB de reducción al cierre. El informe exigía un mínimo de 18 dB. Se conserva margen adicional.
- Fade musical final por pieza y mezcla normalizada en dos pasadas; las mediciones válidas son las del AAC decodificado, no solo el WAV.
- Se encontró y corrigió un fallo de redondeo ASS que podía escribir `02.100` en lugar de `03.00`. Se regeneró el tramo afectado, se añadieron pruebas de acarreo y se revisaron todos los ASS de voces.

## Nueva revisión completa

Se volvió a comprobar cada uno de los diez MP4 completos: 1080×1920, 30 fps, H.264 High/yuv420p, Rec.709, AAC-LC estéreo 48 kHz, duración/fotogramas, decodificación integral, faststart, fondo, loudness/picos, conservación de originales y geometría de textos. Los resultados actuales están en `comprobaciones/resumen_qa_con_voz.json` y los logs por producto. Los diez pasan las comprobaciones técnicas.

La mezcla final queda entre −16,29 y −16,16 LUFS, con picos verdaderos entre −2,20 y −2,10 dBTP. No hay timestamps inválidos, desbordes o intersecciones de texto registrados. Un agente independiente comprobó los diez hashes finales y verificó el cierre del fallo de timestamps.

También se ejecutaron dos contrastes ASR locales, Whisper tiny y base, sobre las diez piezas. Tiny confundió especialmente marcas y cifras; base recuperó con mayor claridad el contenido general, incluido el sesenta y ocho de Dental. Ambos producen errores como «integral médica», «Kotisa» o «Previsemos». No se corrigió el guion para imitar errores del reconocedor ni se declaró aprobada la pronunciación por este contraste. V01 se contrastó además por bloques de 25 y 5 segundos para cubrir toda la pieza dentro del límite de 30 segundos del motor ASR, separando la cola de padding del AAC. Se conservan los resultados y límites de método.

## Lo que sigue pendiente

No se han resuelto por esta actualización las ocho tomas fuente ausentes, las licencias de stock, los logos oficiales/autorización por producto, las fichas vigentes, los tres JSON fuente originales, la prueba móvil y la conexión real de WhatsApp/Meta. La escucha humana de voz y sincronía perceptiva siguen pendientes. No se publicaron anuncios ni se activaron campañas.

Los videos nuevos llevan «REVISIÓN INTERNA · NO PUBLICAR» y «Voz sintética · marca pendiente». Son pruebas avanzadas de montaje y audio, no anuncios finales aprobados ni una garantía de ventas. La lista de recursos pendientes continúa en `../FALTANTES.md`; las mejoras futuras orientadas a consultas pertinentes y ventas están en `../REVISION_FINAL_Y_MEJORAS_VENTAS.md`. La prioridad de producir voz quedó ejecutada; ahora corresponde evaluar su resultado perceptivo junto con los recursos definitivos.

## Archivos y reproducción

- `escenas/`: WAV PCM24 de las sesenta frases.
- `*_locucion_ajustada.wav`: diez locuciones completas a 48 kHz, editables.
- `*.ass` y `*.srt`: subtítulos con tiempos del modelo.
- `secuencias_con_voz_v2.json`: nuevo montaje y registro de retiming.
- `comprobaciones/`: mediciones, mezcla voz/música, ASR, capturas y revisiones.
- `licencias/`: evidencia de procedencia y licencias de síntesis y ASR.

Los modelos se guardan fuera del repositorio en `/workspace/bupa-tts-models`; puede cambiarse con `BUPA_TTS_MODELS`. No se suben binarios de modelos a GitHub. Para otro entorno con FFmpeg/FFprobe y Python3.12:

    python -m venv /tmp/bupa-voz-venv
    /tmp/bupa-voz-venv/bin/pip install -r voces_kokoro/requirements.txt
    /tmp/bupa-voz-venv/bin/python voces_kokoro/preparar_modelos.py
    /tmp/bupa-voz-venv/bin/python voces_kokoro/generar_voces.py
    /tmp/bupa-voz-venv/bin/python voces_kokoro/integrar.py
    /tmp/bupa-voz-venv/bin/python voces_kokoro/verificar_con_voz.py

La integración puede repetirse sin descargar modelos si se conservan los WAV por escena entregados. Para repetir el contraste ASR, ejecutar primero `preparar_modelos.py --asr` y después `reconocer_audio.py base`. La caché de integración se valida con huella de imagen, ASS y comando, y los MP4 se mezclan de nuevo. Los pasos no publican nada ni escriben sobre los originales.
