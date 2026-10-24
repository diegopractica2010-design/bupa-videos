# Entrega de videos corregidos

24 de octubre de 2026. **Producción de revisión interna; aprobación comercial pendiente.** No se publicaron anuncios, activaron campañas ni enviaron mensajes.

## Resultado y cambios

Se produjeron diez videos verticales nuevos, uno por producto, con sesenta escenas y 288 segundos totales. Los cierres duran cinco segundos y mantienen visible **WhatsApp: +56 9 8612 1803**. Cada enlace conserva el mensaje específico del producto.

Las aperturas adelantan el beneficio y el público; los porcentajes se presentan con su base de cálculo y condiciones. Se diferencian copago, arancel y requisitos; Pymes separa titulares de adhesión y la nota 50% de IntegraMédica no se transforma en una promesa universal. No se inventaron precios, condiciones, logos o representación profesional.

La dirección gráfica es original: noventa artes con sus SVG y PNG, sin depender de los clips ausentes del PC. Se retiraron del montaje los marcadores de archivos o tomas pendientes. La denominación del producto aparece en texto, sin fabricar logos. Se conservó el aviso discreto de revisión interna porque faltan validaciones comerciales.

Las locuciones sintéticas completas, música original, subtítulos ASS/SRT y pistas separadas de voz están incluidos. Una frase de cierre demasiado larga se reformuló para que cupiera sin cortar palabras ni superar la velocidad prevista. Los tiempos se calcularon desde el audio, con lectura adicional para condiciones.

La revisión independiente sumó las perspectivas simuladas de cliente, asesor senior y descubrimiento en Instagram. Identificó y corrigió la ausencia de una etiqueta fija WhatsApp en el cierre. La reconstrucción limpia detectó otra incidencia: los nombres internos de las TTF provocaban sustitución tipográfica. Se corrigió su metadata conservando glifos y métricas, se aisló Fontconfig y se añadió una guarda que rechaza fuentes sustitutas en los subtítulos.

## Comprobaciones y evidencia

El resultado aplicable es el de los **MP4 exactos cuyo SHA256 figura en [revision/qa/resumen.json](revision/qa/resumen.json)**; no un archivo anterior con el mismo nombre. El render invalida el QA previo antes de empezar. Un resultado de piloto es histórico y no reemplaza la comprobación integral final.

- 1080 × 1920; H.264 High/yuv420p; 30 fps constantes y 8.640 fotogramas totales; Rec.709; faststart.
- AAC-LC estéreo a 48 kHz; medición posterior del audio exportado, no solamente del WAV de mezcla. Objetivo −16 ± 1 LUFS-I y pico verdadero ≤ −1,5 dBTP.
- Decodificación completa, integridad de tiempos, ausencia de intervalos negros accidentales según umbral documentado y correspondencia con los archivos fuente vigentes.
- Sesenta locuciones completas, velocidad ≤ 1,05×, ventanas suficientes y cierre de cinco segundos. Música al menos 21 dB RMS bajo voz y 24 dB en el cierre antes de loudnorm.
- Texto literal y orden temporal de ASS/SRT; dos líneas como máximo, ancho real y fuente Montserrat entregada. Los tiempos del modelo requieren contraste perceptivo humano.
- Geometría de 520 bloques, márgenes, reserva de subtítulos y ausencia de colisiones; capturas de las seis escenas por producto y cierres reales.
- Concordancia de guiones/secuencias/layout, hashes de imágenes/audio/fuentes/música/código y MP4; contraste ASR independiente como evidencia auxiliar.
- Reconstrucción de Complementa desde una copia limpia, con caché separada, sin el proyecto anterior ni archivos del PC; regeneración musical desde código.

Resultados detallados: [informe técnico](revision/informe_tecnico_final.md), [revisión creativa](revision/revision_creativa_final.md), [revisión comercial](revision/analisis_comercial_final.md) y [reproducción limpia](revision/reproduccion_limpia.md). La comparación del render limpio distingue conformidad técnica de identidad binaria; no se promete exportación bit a bit idéntica entre entornos.

El ASR puede confundir «Revisa», nombres de marca o cifras. Sus transcripciones no se usan para aprobar cada palabra, afirmar naturalidad o certificar la voz. Una inspección de capturas tampoco equivale a ver y escuchar la reproducción continua en un teléfono.

## Editables y conservación

Se entregan JSON de contenido/secuencias/afirmaciones, SVG, PNG, sesenta WAV de escenas, diez pistas completas de voz, veinte archivos ASS/SRT, composición musical y código Python/FFmpeg. [README.md](README.md) explica cómo regenerarlos y qué dependencias se necesitan. No se entrega un proyecto propietario de Premiere o After Effects.

Los PDF y DOCX de entrada se conservan en `fuentes/`. Las versiones anteriores se retiran del árbol actual del repositorio después de verificar el respaldo externo completo de 1.947 archivos, incluidos los diez originales intactos. [Conservación y recuperación](revision/CONSERVACION.md). No se purga el historial Git.

## Lo que falta y lo que todavía puede mejorar ventas

La [lista completa de archivos y validaciones pendientes](VALIDACIONES_PENDIENTES.md) distingue faltantes originales de recursos ya resueltos. Faltan fichas/condiciones vigentes y aclaraciones específicas, identidad/conformidad de marca, escucha y comprensión móvil reales y prueba de apertura/cuenta de WhatsApp. El acceso a fuentes oficiales por la red del entorno devolvió HTTP CONNECT403; no se inventó una validación vigente.

El plan ejecuta el trabajo independiente de esos bloqueos; no los convierte en aprobaciones ficticias. Las 59 afirmaciones siguen `approved: false` hasta contar con evidencia y responsable reales. Los mensajes y el número se verificaron como datos; no se enviaron mensajes.

Después de validar esos puntos, la siguiente mejora orientada a ventas es probar comprensión real y una sola hipótesis por producto, conservando condiciones. La [lista de diez hipótesis](revision/recomendaciones_ventas_pendientes.json) y el [registro de medición futura](contenido/medicion_futura.json) separan consultas pertinentes, cotizaciones y contrataciones. No hay datos reales de rendimiento ni ventas garantizadas. No es posible demostrar que un video sea imposible de mejorar.
