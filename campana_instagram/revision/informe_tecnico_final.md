# Verificación técnica de la entrega actual

Se verificaron los diez MP4 exactos listados en `qa/resumen.json`. Resultado: **10/10 PASS técnico**. Esto no certifica vigencia comercial, escucha humana, lectura en un teléfono real ni resultados de ventas. El estado sigue siendo revisión interna, sin publicación autorizada.

## Evidencia por archivo

| Video | Duración | LUFS-I mezcla AAC | Pico verdadero dBTP | Técnico | SHA-256 abreviado |
|---|---:|---:|---:|---|---|
| V01 | 30 s | -16.13 | -2.14 | PASS | `33a35e2a1ed5c782` |
| V02 | 28 s | -16.27 | -2.13 | PASS | `78270d6241bb8501` |
| V03 | 28 s | -16.29 | -2.18 | PASS | `dc6e3d5ac68da21d` |
| V04 | 28 s | -16.19 | -2.18 | PASS | `ecd4a52e3e4badf8` |
| V05 | 28 s | -16.22 | -2.16 | PASS | `bb9994088ec95639` |
| V06 | 28 s | -16.20 | -2.11 | PASS | `08e2db1f5b123490` |
| V07 | 30 s | -16.23 | -2.15 | PASS | `ca8d27ef0c89c777` |
| V08 | 30 s | -16.22 | -2.08 | PASS | `ba719c02905371ba` |
| V09 | 30 s | -16.12 | -2.06 | PASS | `04b04e1872cf49ed` |
| V10 | 28 s | -16.20 | -2.10 | PASS | `a14209ef7cdbd41a` |

Los SHA-256 completos y las rutas están en `qa/resumen.json` y en el `resultado.json` de cada producto. Antes de empaquetar o publicar, comparar los archivos con esos hashes.

## Comprobaciones realizadas

- 1080 × 1920, H.264 High, yuv420p, 30 fps; conteo de fotogramas y cadencia real por marcas de tiempo. Rec.709 y rango limitado declarados y conversión de imagen RGB en el render. MP4 con faststart.
- AAC-LC, estéreo 48 kHz, decodificación completa sin errores. Sonoridad medida sobre el AAC entregado dentro de −16 ± 1 LUFS-I y pico verdadero ≤ −1,5 dBTP. No se detectaron intervalos negros accidentales de al menos 0,1 s según el umbral documentado en verificar.py.
- Voz original de síntesis íntegra dentro de la ventana de cada escena, velocidad ≤ 1,05, sin cortar palabras para encajar. Mezcla previa a loudnorm con voz ≥ 21 dB RMS sobre música por escena y ≥ 24 dB en el cierre. El informe distingue esta medición de la medición del AAC final.
- Subtítulos ASS y SRT con texto literal del guion hablado, orden temporal válido y concordancia entre relojes. Máximo dos líneas de 32 caracteres, fuente de 48 px y ajuste por ancho real. Sus tiempos proceden del modelo de voz; requieren escucha para certificar sincronía perceptiva.
- Concordancia de los diez guiones editables con las sesenta escenas de secuencias; hash del guion asociado al layout vigente. Geometría de los 520 bloques, reserva de subtítulos, márgenes seguros y ausencia de colisiones geométricas.
- Fuente de subtítulos confirmada por libass en los 74 segmentos: selección real `Montserrat-Bold`, sin fallback a fuentes del host. Fontconfig aislado a las fuentes entregadas; QA exige esta evidencia por segmento, además de comparar los hashes TTF. La tabla de nombres de las instancias estáticas fue corregida sin modificar glifos ni métricas; procedencia y comprobaciones en `recursos/fuentes/correccion_metadata.json`.
- Hashes del MP4 al inicio y al final de QA; correspondencia con el render y con los audios, imágenes, fuentes, música y código vigentes. Se invalidan los resultados de QA anteriores al iniciar un nuevo render.
- Sesenta fotogramas extraídos de los MP4, uno por escena, con diez hojas de contacto. Las hojas sirven al muestreo visual y no reemplazan reproducción continua en un móvil.

## Incidencias corregidas durante esta ejecución

1. El render esperaba PNG en subcarpetas por producto, mientras el generador produce `recursos/graficos/Vxx-Sxx.png`. Se unificó el render con la estructura real y se repitió la exportación.
2. Los cierres mostraban un número sin etiqueta fija del canal. Se añadieron «WhatsApp: +56 9 8612 1803» en los diez cierres; se renderizaron y verificaron nuevamente los diez MP4. La caché reutilizó únicamente escenas intactas y comprobadas.
3. Se añadió comprobación del guion editable frente a secuencias y del hash de origen del layout. Se invalidó el resumen de QA previo al comenzar cada nuevo render para impedir aceptar un PASS obsoleto.

4. La reproducción desde una copia limpia detectó que libass usaba una fuente del host: las TTF estáticas conservaban nombres internos de la instancia Thin. Se corrigieron esos nombres, se aisló Fontconfig y se añadieron guardas del nombre real seleccionado en render y QA. Se volvieron a renderizar y verificar los diez MP4; las 74 selecciones actuales corresponden a la TTF Bold entregada.

## Comprobaciones pendientes fuera del QA automático

Escucha humana de pronunciación, acento, naturalidad y sincronía; reproducción completa y lectura con interfaz real de Instagram; apertura del destino de WhatsApp sin enviar mensajes; fichas comerciales vigentes y autorización de identidad/marca. No se han activado anuncios ni campañas. La evaluación automática no permite prometer ventas ni perfección absoluta.
