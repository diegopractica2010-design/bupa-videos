# Conservación de originales y versiones anteriores

Antes de modificar la entrega se creó un respaldo íntegro fuera del checkout:

`/workspace/respaldos_bupa/antes_renovacion_c4adaeb.tar`

Incluye los diez MP4 originales, el proyecto anterior completo, los archivos ignorados y el historial `.git` del commit base `c4adaeb184ccaec9ee9d2a863ad462fe94fc7a6f`. Cada uno de los 1.947 archivos del TAR se comparó mediante SHA256 con el inventario inicial. Antes de retirar los árboles viejos se repitió la comprobación completa y se cotejaron nuevamente los diez originales actuales con sus copias archivadas.

Los hashes, tamaños y rutas de recuperación están en [conservacion.json](conservacion.json). El inventario íntegro externo está en `/workspace/respaldos_bupa/inventario_antes_renovacion.json`.

Para recuperar los originales en **otra carpeta**, sin sobrescribir la nueva entrega:

```bash
mkdir -p /workspace/recuperacion_bupa
tar -xf /workspace/respaldos_bupa/antes_renovacion_c4adaeb.tar \
    -C /workspace/recuperacion_bupa bupa-videos/output
```

El archivo externo pertenece a este entorno de nube; no es una segunda copia alojada en GitHub. La historia de GitHub también conserva los commits anteriores porque no se reescribe ni purga el historial. La limpieza solicitada retira `output/` y `edicion_instagram_v1/` del árbol de la rama actual; conserva los informes de entrada como evidencia dentro de la nueva entrega.
