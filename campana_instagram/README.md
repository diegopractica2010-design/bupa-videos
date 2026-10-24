# Entrega actual de Instagram y WhatsApp

Diez productos, sesenta escenas y un cierre de cinco segundos por pieza. Destino confirmado: **+56 9 8612 1803**, con mensaje específico de cada producto. Los videos son candidatos de revisión interna; no se autoriza ni ejecuta su publicación.

## Archivos

| Carpeta | Contenido |
| --- | --- |
| `videos/` | Diez MP4 actuales, sin exports antiguos. |
| `contenido/` | Guiones, notas, tarjetas, captions, afirmaciones, mensajes y secuencias editables. |
| `recursos/graficos/` | Noventa PNG y noventa SVG originales, regenerables desde los guiones. |
| `audio/escenas/` | Sesenta WAV de voz con tiempos nativos por palabra y caché de texto. |
| `audio/locuciones/` | Diez pistas completas de voz, separadas de la música. |
| `subtitulos/` | Diez ASS y diez SRT editables. ASS quemado en el video, SRT como archivo de intercambio. |
| `recursos/audio/` | Música original sintetizada; código de composición incluido. |
| `recursos/fuentes/`, `recursos/licencias/` | Montserrat y documentación de procedencia/licencias de herramientas y modelos. |
| `fuentes/` | Informes PDF/DOCX recibidos, conservados como evidencia de entrada. |
| `revision/` | QA por hash, capturas de los MP4 reales, incidencias y revisiones independientes. |
| `plan/` | Plan maestro, ejecución y diagnóstico que motivó la nueva versión. |

Consulta [ENTREGA.md](ENTREGA.md) y [VALIDACIONES_PENDIENTES.md](VALIDACIONES_PENDIENTES.md) para separar trabajo realizado de validaciones externas. No contiene proyecto propietario de Premiere/After Effects: los editables entregados son JSON, SVG, WAV, ASS/SRT y código Python/FFmpeg.

## Reproducir en la nube

Entorno comprobado: Linux, Python 3.12 y FFmpeg 7.1.5 con libx264 y libass, sin depender del PC. Los WAV, música, fuentes y gráficos ya están incluidos: para volver a montar no hace falta sintetizar voz ni descargar modelos.

Desde esta carpeta:

```bash
python3 -m venv /tmp/bupa-video-venv
/tmp/bupa-video-venv/bin/pip install -r herramientas/requirements.txt
/tmp/bupa-video-venv/bin/python herramientas/renderizar.py
/tmp/bupa-video-venv/bin/python herramientas/verificar.py
```

`renderizar.py --only V03` permite regenerar un producto. `verificar.py` comprueba el conjunto de diez y rechaza una entrega parcial, fuentes desactualizadas o un MP4 cuyo hash no corresponda. La caché queda en `/tmp/bupa_v3_render`, fuera del proyecto. Cambiar el código del renderizador requiere regenerar los registros de render antes del QA.

Después de editar un guion, se regeneran todas las capas afectadas:

```bash
export BUPA_TTS_MODELS=/tmp/bupa-modelos
/tmp/bupa-video-venv/bin/python herramientas/descargar_modelos.py
/tmp/bupa-video-venv/bin/python herramientas/sintetizar.py
/tmp/bupa-video-venv/bin/python herramientas/graficos.py
/tmp/bupa-video-venv/bin/python herramientas/renderizar.py
/tmp/bupa-video-venv/bin/python herramientas/verificar.py
```

Las descargas usan las URL documentadas, verifican SHA256 y respetan el proxy/TLS. No se incluyen pesos de modelos en Git. Para el contraste ASR auxiliar: `descargar_modelos.py --asr` y `contrastar_asr.py`. El ASR no certifica pronunciación ni reemplaza una escucha humana.

La composición musical se puede regenerar con `generar_musica.py`; `--stems` exporta sus cinco pistas separadas al destino elegido. No hay samples externos ni voces clonadas. Las licencias de herramientas/modelos no equivalen a autorización de la marca para publicar.

## Alcance de la revisión

Los controles automáticos comprueban codificación, cuadros/tiempos, decodificación, mezcla final AAC, subtítulos, geometría y correspondencia con archivos fuente. Las revisiones de agentes son simuladas y visuales/textuales; no son entrevistas reales ni certificaciones comerciales. Las escuchas humanas, comprensión móvil, ficha vigente, identidad del asesor y autorización de marca se registran aparte. Ninguna métrica de ventas fue inventada.
