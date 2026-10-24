# Reproducción desde una copia limpia

Fecha UTC: 2026-10-24T13:12:59.527455+00:00. Se copió únicamente `campana_instagram/` a un directorio nuevo, sin `__pycache__`, y se reconstruyó **V03 Complementa** con una caché independiente. Se usaron los WAV, gráficos y fuentes de la entrega: no se necesitaron `output/`, `edicion_instagram_v1/`, el PC, modelos de voz ni servicios externos. El entorno Python/FFmpeg fue el mismo de la nube; esto no acredita una instalación en otro sistema ni la reconstrucción independiente de los otros nueve productos.

## Resultado

- 19/19 controles técnicos del MP4 reconstruido aprobados, incluida selección de la fuente entregada sin fallback del host.
- Entradas de render idénticas a las del V03 entregado; renderer y recursos relevantes permanecieron iguales durante la prueba. El verificador actualizado solo renombró una clave del resultado y se volvió a ejecutar.
- Audio decodificado idéntico, SHA256 `c0e80baaeccf3b8d535da25d8e5b92e4fdf3f3af1c4ad29c026013ee6dc48e08`.
- Comparación de todos los fotogramas: SSIM `0.999995`. El MP4 reconstruido **no es idéntico byte por byte**; no se promete determinismo binario. Ambos cumplen la especificación técnica.
- Música regenerada desde `generar_musica.py`: archivo WAV idéntico, SHA256 `6edf1efbc8345496b3a516a9dc7cb45a157ae9e8cdb8f9bd9e869ba3e36f1e2f`.

MP4 reconstruido: `dbb8200c72fbacfda4d5ba8273a82dd70eea5eeb0612e282d2acc61c01a5c871`. MP4 de entrega comparado: `dc6e3d5ac68da21d7be2d72a3b4036577ab396f7272f529c05b163696391959b`. Comandos, hashes, controles y selección de fuentes por segmento están en [reproduccion_limpia.json](reproduccion_limpia.json). Logs completos y comparaciones temporales: `/tmp/bupa_entrega_limpia_final`.

## Incidencia encontrada y cerrada

La primera prueba detectó una dependencia no declarada: las dos instancias estáticas de Montserrat conservaban nombres internos de Thin/Regular y libass elegía OpenAI Sans del host. El QA anterior no comprobaba esa selección. Se corrigieron los nombres sin cambiar glifos ni métricas, se aisló Fontconfig y se añadió una guarda de la fuente elegida. La prueba completa de V03 se repitió desde otra copia limpia con la corrección y pasó. La selección registrada ahora es `Montserrat-Bold`, sin fallback del sistema.

No se realizó escucha humana, prueba móvil ni validación comercial a través de esta prueba.
