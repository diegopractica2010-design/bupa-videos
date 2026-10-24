# Revisión creativa de la nueva entrega

24 de octubre de 2026. Revisión asistida de archivos reales, no entrevista de clientes ni aprobación comercial.

## Artes fuente comprobadas

Se inspeccionaron las 60 escenas principales y las 30 variantes de detalle, mediante contactos visuales de los PNG reales. Se ampliaron además V04-S01, V07-S03 y V08-S04 por su densidad y riesgo de interpretación. Los 90 SVG corresponden a los mismos trazados y textos del generador; no se afirma equivalencia de renderizado en cualquier editor SVG.

Fuente de contenido SHA256: `12c9901798db1aad52e3e81b5c0d20cc0057bf45f09a094b3ff83af06f9d6f62`. El informe de geometría registra 520 bloques y 0 errores. El generador usa producto a 40/64 px, titulares 64 px, tarjetas 36 px y notas 32 px; reserva la franja x96/y930/ancho864/alto140 para subtítulos.

- Sin textos cortados, colisiones detectadas ni condiciones sustituidas por letra más pequeña en las artes inspeccionadas.
- Las tres categorías de Cuidado Total se muestran en filas de ancho completo; «Hospitalización» permanece íntegra.
- Pymes diferencia las alternativas desde 5 titulares y plan 80% desde 15. La adhesión mínima 80% tiene una escena propia y no se muestra como porcentaje de cobertura.
- IntegraMédica 100% conserva el ámbito ambulatorio y el tope UF60; la nota de bonificación 50% aparece con su condición literal, sin inventar su relación jurídica con el 100%. Su interpretación comercial continúa bloqueada hasta la ficha aplicable.
- Dental conserva «descuento sobre arancel» junto a 68%; no transforma el porcentaje en un precio final.
- Las escenas de cierre contienen producto, propósito de consulta y la etiqueta fija «WhatsApp: +56 9 8612 1803». Se corrigió la ambigüedad del número sin canal: el subtítulo temporal por sí solo no identificaba WhatsApp durante los cinco segundos completos. La etiqueta ocupa 617,44 de 864 píxeles disponibles a 44 px. Es texto, no un botón ficticio clicable dentro del MP4.
- Gráficos propios, sin falsificación de logos, pacientes, testimonios o credenciales del asesor. La denominación comercial sigue sujeta a conformidad de marca.
- La variante de detalle conserva los textos y tarjetas; elimina iconos ornamentales para cambiar la composición sin agregar promesas.

## Revisión de los MP4

Se inspeccionaron **60 fotogramas reales de los diez MP4**, uno por escena, extraídos por el QA en `revision/qa/<producto>/contacto_6_escenas.jpg`. Incluyen subtítulos y la codificación final. Se repitió la inspección después de corregir los cierres y, de nuevo, después de corregir la selección de la tipografía de los subtítulos. Los fotogramas son muestras por escena; este control no equivale a una reproducción humana continua.

Los diez cierres muestran la etiqueta fija «WhatsApp: +56 9 8612 1803», sin colisionar con CTA, subtítulos o nota. En Dental, el CTA ocupa dos líneas y conserva separación respecto al canal/número. Las tarjetas de Cuidado Total permanecen completas y las condiciones de Pymes e IntegraMédica 100% se conservan en sus escenas. Ninguna muestra presenta nombres de archivo, marcadores de tomas/logos ausentes, texto truncado o superposición de texto detectada.

Se confirmó que cada hash de MP4 coincide con su informe de render y que el informe incluye los hashes actuales de las dos fuentes TTF y de la gráfica de cierre. Los caracteres españoles, porcentajes y nombres de producto son íntegros en las nuevas muestras; las dos líneas de subtítulos permanecen separadas de notas/tarjetas. El QA verifica Montserrat real sin sustitución de fuente en los 74 segmentos codificados. QA automático completo indica `COMPLETE / technical_pass=true` para esta entrega.

| ID | Archivo | SHA256 inspeccionado | Resultado de la muestra visual |
| --- | --- | --- | --- |
| V01 | `bupa_adulto_mayor_70.mp4` | `33a35e2a1ed5c782e5b11344e22a90529bb2da8ca66e7c3992f03fb4934893d3` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V02 | `bupa_catastrofico.mp4` | `78270d6241bb8501115fa0d516af070c9cf9ba5699898e765bcc9f84169775d9` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V03 | `bupa_complementa.mp4` | `dc6e3d5ac68da21d7be2d72a3b4036577ab396f7272f529c05b163696391959b` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V04 | `bupa_cuidado_total.mp4` | `ecd4a52e3e4badf867b8dfdd259ca10cbd1425d8d9ebbc4af651d7c3cc1f39eb` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V05 | `bupa_multisalud.mp4` | `bb9994088ec95639db32995a02e1c31679f03312970f4474472d559d5f1dbf11` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V06 | `bupa_proteccion.mp4` | `08e2db1f5b1234903f6a5e6b05811c4dc2af80d0b6dcea3c94be725b9ce53113` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V07 | `bupa_pymes.mp4` | `ca8d27ef0c89c777f522473faa0022296ba66883241d942631fdff6a186a688c` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V08 | `integramedica_100.mp4` | `ba719c02905371babedea4b91f2f5153c5348b1d0632a8dd8c81588b35efd007` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V09 | `mi_dental_integramedica.mp4` | `04b04e1872cf49ed6f099678cfb677d0ca0861e56305cca6b03dd4832cd08bd5` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |
| V10 | `seguros_global.mp4` | `a14209ef7cdbd41ae06f0f7b5b3916d2eb6c133b9b60a7d5750e575e30fc36d7` | Montserrat correcta; 6 escenas sin defecto visual necesario en la muestra |

## Incidencia ejecutable corregida

**CR-01 — Canal de contacto fijo en cierre.** Un número sin etiqueta podía interpretarse como llamada cuando desaparecía el subtítulo. Corrección en el generador: añadir «WhatsApp:» al número, conservando tamaño 44 px, posición y duración. Solo se modificaron los diez SVG/PNG de cierre, se regeneraron los diez MP4 y se inspeccionaron sus nuevas muestras. **Cerrada** con los hashes anteriores. No se inventó un botón dentro del MP4 ni se enviaron mensajes.

**CR-02 — Sustitución silenciosa de tipografía en subtítulos.** La reconstrucción limpia detectó selección de una fuente ajena en libass. Las instancias TTF tenían pesos reales 700/800 pero nombres internos «Thin/Regular» y banderas de regular. Se corrigieron nombres y banderas conservando idénticas las once tablas de glifos, métricas y composición, además de una comprobación de bitmap y avance con caracteres españoles. `fc-scan` identifica ahora Montserrat Bold y Montserrat ExtraBold. Procedencia completa en `recursos/fuentes/correccion_metadata.json`. **Cerrada:** selección real de Montserrat-Bold comprobada en los 74 segmentos, los diez MP4 regenerados y los 60 fotogramas inspeccionados nuevamente. El control `subtitle_font_no_host_fallback` pasa en los diez informes finales. Los hashes de la tabla corresponden a esta última pasada.

**Resultado del alcance visual:** cero defectos visuales necesarios conocidos en las artes y muestras de MP4 inspeccionadas. No certifica condiciones comerciales, naturalidad de voz, sincronía perceptiva o lectura real en móvil.

## Límites y mejoras opcionales

La claridad visual no acredita ventas ni una calidad «imposible de mejorar». La lectura en teléfono real con la interfaz de Instagram y la escucha continua requieren comprobación humana; reducir un contacto visual no la sustituye.

Una variante futura con material humano autorizado podría aportar identificación emocional, pero necesita procedencia y permisos. Es una hipótesis creativa y no una dependencia del montaje gráfico actual. La prioridad comercial previa a publicar sigue siendo verificar fichas, identidad de quien atiende y uso de marca; añadir estímulos visuales no resuelve esos bloqueos.
