# Edición Instagram / WhatsApp · entrega parcial de revisión

Estado: pruebas internas renderizadas, NO versiones finales ni aprobadas para publicación. No se publicaron anuncios, no se activaron campañas y no se enviaron mensajes. Guardar estos entregables en GitHub no publica anuncios ni activa campañas.

## Material comprobado

Los 10 MP4 originales están en ../output. Se conservan intactos: los SHA256 se registran antes y después y coinciden con el Anexo B de la auditoría. FFmpeg, FFprobe y Python están disponibles en la nube. El trabajo realizado no utiliza herramientas del PC ni requiere mantenerlo encendido. Las tomas y archivos fuente que solo están en el PC no se han transferido y no se pueden utilizar desde aquí.

Se leyeron el PDF y el DOCX adjuntos; se extrajeron los 10 guiones, 60 escenas, 100 órdenes y mensajes específicos del Anexo A. Los archivos originales plan_maestro.json, ordenes_ejecucion.json y enlaces_whatsapp.json y auditoria/evidencias NO estaban disponibles. Los JSON nuevos se identifican expresamente como reconstrucciones del DOCX, no copias de esos archivos. El contraste con ellos permanece pendiente.

## Entregables

- renders_revision/: 10 MP4 de revisión, 1080×1920, 30 fps, H.264 High, yuv420p, SDR Rec.709, AAC-LC estéreo 48 kHz. Todos llevan aviso visible NO PUBLICAR. El tamaño/bitrate real varía por complejidad; el objetivo de codificación es 10 Mbps, máximo configurado 14 Mbps, sin relleno artificial de bitrate.
- editables/: generador Python, verificador, secuencias JSON, ASS y SRT PROVISIONALES, captions y mensajes de WhatsApp. Los subtítulos son texto de guion con tiempos de lectura estimados, NO una sincronización validada contra voz.
- recursos/: SVG y PNG por escena; los SVG son editables y requieren la familia Montserrat incluida. Música original y cinco stems separados de pluck, bajo, bombo, aro y shaker. No son pistas compradas ni copias del audio original. Los eventos sintéticos terminan con una cola a cero de 20 ms para evitar cortes abruptos.
- fuentes/: informes recibidos y extracción trazable de su contenido.
- comprobaciones/: registro de las 100 órdenes y resultados automáticos, ffprobe, decodificación completa, loudness de música y hojas de contacto por pieza. Consultar resumen_qa.json para resultados efectivos.

## Cambios efectivamente realizados

Las pruebas se reconstruyeron desde cero: no se conservaron imágenes con subtítulos quemados ni locuciones/promesas incorrectas del original. Se aplicaron los guiones y duraciones del informe, identidad escrita desde el inicio, notas legales breves, cierre de cinco segundos, número +56 9 8612 1803 y mensajes por producto reconstruidos y cotejados literalmente con el Anexo A. Los enlaces no son botones incrustados ni se prueban enviando mensajes.

Se dibujaron gráficos propios según las órdenes: escudos, documentos, consulta/examen/cama, tarjetas de Isapre/copago/complemento, red, titulares, calendario, diente y silueta mundial estilizada sin países resaltados. Las tomas fuente de 12 escenas no estaban presentes: sus posiciones llevan marcadores de recurso pendiente, NO material sustituto presentado como definitivo. Las 48 escenas restantes tienen la base gráfica o cierre definido; todas siguen pendientes de voz y marca.

Se produjo campana_salud_112bpm.wav: 112 BPM, 4/4, C–Am–F–G, dos compases por acorde, pluck y bajo sintéticos, bombo suave, aro y shaker originales. Sin whoosh, riser, impact ni ding. Los MP4 contienen únicamente esta música, normalizada en dos pasadas a objetivo −16 LUFS y pico verdadero ≤−1,5 dBTP, con cierre reducido 3 dB. Se dejó margen de pico adicional antes de AAC para que el archivo final cumpla el límite; la medición válida es la del MP4 decodificado. Estas mediciones NO acreditan la mezcla de voz: no hay narración. El stem original conserva sus niveles de producción para mezclar con una futura voz autorizada.

## Bloqueos que se respetaron

B01: faltan logos oficiales y conformidad por familia. La caja de marca muestra “Logo pendiente”. No se fabricó un logo con tipografía ni se recortó Global.
B02: faltan clips limpios y comprobantes de procedencia/licencia. No se descargó stock arbitrario ni se extrajeron personas del video final para ocultar textos.
B03: falta validar vigencia del producto/ficha y autorizar una voz comercial. No se clonó ni sintetizó una voz pendiente de derechos. No se añadieron precios ni nuevas condiciones.
B04: faltan locución, sincronía ±100 ms, mezcla voz/música (música ≥18 dB bajo voz), escucha humana, validación móvil y revisión final del montaje con los recursos reales.
B05: enlaces y número se comprobaron estructuralmente; falta abrir cada destino en un teléfono y verificar la conexión de cuenta/botón sin enviar mensajes.
B06: rendimiento comercial no medido ni garantizado.
B07: falta validar especificaciones y configuración vigente de Meta al preparar publicación, fuera del alcance de esta entrega.

No se sustituye la falta de una autorización con el silencio del usuario. El usuario confirmó que apagó el PC e indicó continuar con el material disponible y detallar los archivos faltantes en la entrega. Se avanzó con las tareas independientes ya autorizadas y con marcadores explícitos para los elementos bloqueados.

## Reproducir

Desde esta carpeta o cualquier directorio, con Python 3 y FFmpeg/FFprobe accesibles:

    python -m venv /tmp/bupa-video-venv
    /tmp/bupa-video-venv/bin/pip install -r editables/requirements.txt
    /tmp/bupa-video-venv/bin/python editables/producir.py
    /tmp/bupa-video-venv/bin/python editables/verificar.py

No requiere los MP4 originales para renderizar estas pruebas, ni usa sus pistas. El verificador sí requiere ../output para comprobar conservación. No mover ni sobrescribir los originales. Los comandos generan nuevamente únicamente recursos, editables provisionales, renders de revisión y logs dentro de esta carpeta. El generador no inserta stock, voz ni logos aunque se coloquen archivos nuevos: requiere completar el montaje y validación de esos recursos antes de una entrega final.

Las entradas de 180 ms/12 px y salidas de 100 ms se aplican a la capa gráfica al iniciar/terminar la escena; los cortes internos son directos y sin desplazamiento de la capa, sin vaciar el lienzo. Se omitió el header repetido en S02 cuando el producto pasa a título principal. En los cortes internos gráficos indicados se cambia de icono a texto. Se priorizó no solapar títulos, iconos y subtítulos: algunos iconos se sitúan en y820 en presentaciones con título de hasta tres líneas; los titulares funcionales van en y780 en otras escenas. Esta adaptación respecto de coordenadas nominales del informe queda pendiente de conformidad visual. La paleta es una decisión editorial, no un manual de marca autorizado.

Montserrat se obtuvo del repositorio oficial google/fonts (ofl/montserrat), con licencia OFL adjunta; los pesos 700/800 se generaron de la fuente variable. No se alteró la verificación TLS al descargarla. Las formas vectoriales y composición musical se produjeron específicamente para este trabajo.
