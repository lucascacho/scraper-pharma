# pharmacheck — ¿mis productos están en las farmacias online?

Esta herramienta revisa, una por una, las farmacias online más grandes y te dice
**si tus productos aparecen en su web y si están en stock**. Después te arma una
planilla lista para abrir en Excel.

Hoy revisa: **FarmaPlus, Farmacity, FarmaLife y Farmacias del Pueblo**.

Hacerlo a mano son 6 productos × 4 farmacias = 24 búsquedas. Esto tarda menos de un minuto.

---

## 1. Antes de empezar (se hace una sola vez)

Esto hay que hacerlo la primera vez nada más. Una vez que funciona, no lo tocás más.

### Qué necesitás

| | |
|---|---|
| **Internet** | consulta las webs de las farmacias en vivo |
| **Python 3.10 o superior** | el programa está escrito en Python |
| **La librería `requests`** | una pieza extra de Python, se instala en 10 segundos |
| **La carpeta del proyecto** | con `check_stock.py`, `productos.csv` y `farmacias.json` adentro |

### Paso 1 — ¿Tenés Python?

Abrí la terminal y escribí:

```
python3 --version
```

- Si te contesta algo como `Python 3.13.7` (o cualquier número **3.10 o mayor**), listo, pasá al paso 2.
- Si dice `command not found` o te muestra `Python 3.9` o menor, instalá la última versión
  desde [python.org/downloads](https://www.python.org/downloads/) y volvé a probar.

> **En Windows** el comando suele ser `python` en vez de `python3` (y `pip` en vez de `pip3`).
> Si `python3` no anda, probá con `python`. Al instalar desde python.org, tildá la opción
> **"Add Python to PATH"** en la primera pantalla, si no la terminal no lo va a encontrar.

### Paso 2 — Instalar `requests`

```
pip3 install requests
```

Tarda unos segundos. Si te dice `Requirement already satisfied`, ya lo tenías: mejor.

Para confirmar que quedó bien:

```
python3 -c "import requests; print('ok')"
```

Tiene que responder `ok`.

### Paso 3 — Pararte en la carpeta del proyecto

Descomprimí la carpeta del proyecto donde te quede cómodo (Escritorio, Documentos, da igual)
y en la terminal andá hasta ahí con `cd`. Por ejemplo:

```
cd ~/Escritorio/scraper-pharma
```

Para verificar que estás en el lugar correcto:

```
ls
```

Tenés que ver, entre otros, estos tres archivos: `check_stock.py`, `productos.csv` y `farmacias.json`.

### Paso 4 — Prueba rápida

Antes de correr todo, probá con una sola farmacia para confirmar que la conexión funciona:

```
python3 check_stock.py --solo FarmaPlus
```

Si te muestra una tabla con números, ya está todo listo. Si te da errores, mirá el punto 7.

### Y la configuración propiamente dicha

Nada obligatorio: el proyecto viene con 6 productos de ejemplo en `productos.csv` y las
4 farmacias ya configuradas en `farmacias.json`. Cuando quieras poner **tus** productos,
seguí el punto 4; para sumar otra farmacia, el punto 8.

---

## 2. Usarlo (los 3 pasos de siempre)

**Paso 1.** Abrí la terminal en la carpeta del proyecto.

**Paso 2.** Escribí esto y apretá Enter:

```
python3 check_stock.py
```

**Paso 3.** Esperá. Cuando termina te muestra un resumen así:

```
Chequeando 6 producto(s) en 4 farmacia(s): FarmaPlus, Farmacity, FarmaLife, Farmacias del Pueblo

FARMACIA               EN STOCK  SIN STOCK  NO LISTADO  ERROR
--------------------------------------------------------------
FarmaLife                     3          1           2      0
FarmaPlus                     4          1           1      0
Farmacias del Pueblo          1          0           5      0
Farmacity                     3          0           3      0

Detalle: /home/sprite/scraper-pharma/reportes/stock-20260807-2215.csv
Matriz:  /home/sprite/scraper-pharma/reportes/matriz-20260807-2215.csv
```

Esas dos últimas líneas son los archivos que se generaron. **Abrilos con Excel.**

---

## 3. Los dos archivos que genera

Se guardan en la carpeta `reportes/`. El nombre incluye la fecha y la hora
(`20260807-2215` = 7 de agosto de 2026, 22:15), así que nunca se pisan entre sí y
podés comparar cómo cambió la semana pasada contra hoy.

### `matriz-...csv` — el que vas a mirar el 90% de las veces

Una fila por producto, una columna por farmacia. Se lee de un vistazo:

| producto | FarmaLife | FarmaPlus | Farmacias del Pueblo | Farmacity |
|----------|-----------|-----------|----------------------|-----------|
| Enterogermina Plus Ampollas x5 | EN STOCK | SIN STOCK | EN STOCK | EN STOCK |
| Buscapina Antiespasmódico x20 grageas | SIN STOCK | EN STOCK | NO_LISTADO | EN STOCK |
| Buscapina Perlas 50 cápsulas | EN STOCK | EN STOCK | NO_LISTADO | NO_LISTADO |
| Hepatalgina Gotas x120ml | EN STOCK | EN STOCK | NO_LISTADO | EN STOCK |
| Novalgina 500mg x20 comprimidos | NO_LISTADO | NO_LISTADO | NO_LISTADO | NO_LISTADO |

### `stock-...csv` — el detalle

Lo mismo pero con todo: precio, precio de lista, unidades en stock, y el **link
directo al producto** en la web de esa farmacia (columna `url`), por si querés ir a verlo.

### Qué significa cada palabra

| dice | significa | qué hacer |
|------|-----------|-----------|
| **EN STOCK** | está publicado y se puede comprar | nada, todo bien |
| **SIN STOCK** | está publicado pero agotado | avisale al comercial de esa cadena |
| **NO_LISTADO** | esa farmacia no lo tiene en su catálogo | ojo, ver más abajo ⚠️ |
| **ERROR** | no se pudo consultar (se cayó internet, la web bloqueó el pedido) | volvé a correrlo en un rato |
| **(?)** al lado | lo encontró por nombre parecido, no por código de barras | revisá el link y confirmá que sea tu producto |

⚠️ **Cuidado con `NO_LISTADO`.** Si sabés que esa farmacia sí vende el producto, casi
siempre es porque lo cargaron con **otro código de barras**. Ver el punto 5.

---

## 4. Cambiar la lista de productos

Abrí el archivo `productos.csv` con Excel. Se ve así:

| codigo | nombre | ean | alias |
|--------|--------|-----|-------|
| DIST-001 | Enterogermina Plus Ampollas Bebibles x5 x5ml | 7798389330018\|7795312109017 | Enterogermina Plus x5 |
| DIST-006 | Novalgina 500mg x 20 comprimidos | | Novalgina comprimidos |

- **codigo** — tu código interno. Opcional, sirve para cruzar con tu sistema.
- **nombre** — *obligatorio*. Cómo se llama el producto.
- **ean** — el código de barras. Opcional pero **muy recomendable**: es lo que hace
  que la búsqueda sea exacta en vez de aproximada.
- **alias** — otra forma de buscarlo, por si el nombre largo no da resultados.

Agregá las filas que quieras y guardá. La próxima vez que corras el programa, usa la lista nueva.

> **Al guardar desde Excel**, elegí "CSV UTF-8". Y si Excel te transforma el código de
> barras en algo como `7,79839E+12`, marcá la columna `ean` y ponele formato **Texto**
> antes de escribir los números.

---

## 5. El truco importante: un producto, varios códigos de barras

Un mismo producto puede estar cargado con distintos EAN según la cadena. Enterogermina
Plus figura como `7798389330018` en FarmaPlus, pero como `7795312109017` en Farmacias
del Pueblo (es el código de la caja, no el del blíster).

**Si un producto te da `NO_LISTADO` en una farmacia donde vos sabés que está**, buscalo
a mano en la web de esa farmacia, fijate qué código de barras usa, y agregalo en la
columna `ean` **separado con una barra vertical** `|`:

```
7798389330018|7795312109017
```

Se prueban todos. Esto resuelve la enorme mayoría de los `NO_LISTADO` falsos.

---

## 6. Variantes útiles

Todo esto es opcional; con `python3 check_stock.py` solo ya funciona.

```
python3 check_stock.py --solo FarmaPlus
```
Revisar una sola farmacia (mucho más rápido si estás probando algo).

```
python3 check_stock.py --verbose
```
Ir viendo producto por producto mientras trabaja, en vez de esperar callado.

```
python3 check_stock.py --productos otra-lista.csv
```
Usar otra lista de productos en vez de `productos.csv`.

---

## 7. Si algo no anda

**"command not found: python3"** — no está instalado Python (o en Windows, el comando es
`python`). Ver el punto 1, paso 1.

**"No module named 'requests'"** — falta una pieza. Corré una sola vez:
```
pip3 install requests
```

**"can't open file 'check_stock.py'"** — la terminal no está parada en la carpeta del
proyecto. Ver el punto 1, paso 3.

**Muchos `ERROR` en el resumen** — la farmacia está bloqueando los pedidos por venir muy
seguidos. Esperá unos minutos y volvé a correrlo, o hacelo más lento:
```
python3 check_stock.py --demora 1.5
```

**Los acentos se ven raros en Excel** — abrí Excel primero, y después
*Datos → Obtener datos → Desde texto/CSV*, eligiendo codificación UTF-8 y punto y
coma (`;`) como separador.

**Todo da `NO_LISTADO`** — revisá que `productos.csv` tenga la columna `nombre` escrita
así, en minúscula, en la primera fila.

---

## 8. Agregar otra farmacia

Muchas farmacias online argentinas usan la misma plataforma por atrás (VTEX). Si la que
querés sumar es una de esas, alcanza con agregarla a la lista `farmacias.json`.

Para saber si sirve: abrí en el navegador la dirección de la farmacia seguida de
`/api/catalog_system/pub/products/search?ft=ibuprofeno`. Por ejemplo:

```
https://www.farmaplus.com.ar/api/catalog_system/pub/products/search?ft=ibuprofeno
```

Si te muestra un montón de texto con llaves `{` y corchetes `[`, sirve. Si te muestra una
página normal o un error, esa farmacia necesita programación adicional.

Si sirve, abrí `farmacias.json` con cualquier editor de texto y copiá el bloque de una
farmacia existente cambiando el nombre y la dirección:

```json
{
  "nombre": "Farmacia Nueva",
  "tipo": "vtex",
  "base_url": "https://www.farmacianueva.com.ar",
  "activa": true
}
```

Poner `"activa": false` la deja configurada pero la saltea.

---

¿Detalles de implementación, opciones avanzadas, cómo está armado por dentro?
Está todo en **[DOCUMENTACION-TECNICA.md](DOCUMENTACION-TECNICA.md)**.
