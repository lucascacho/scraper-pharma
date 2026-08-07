# pharmacheck — chequeo de stock en farmacias online

Verifica si tus productos **figuran** en el catálogo de cada farmacia y si **tienen stock**,
para todas las farmacias configuradas, y arma un CSV listo para abrir en Excel.

## Uso rápido

```bash
python3 check_stock.py                          # chequea productos.csv en todas las farmacias activas
python3 check_stock.py --verbose                # muestra el avance producto por producto
python3 check_stock.py --solo FarmaPlus         # una sola farmacia
python3 check_stock.py --productos catalogo.csv --salida reportes/
```

Requiere Python 3.10+ y `requests` (ya instalado en este entorno).

## Tu catálogo: `productos.csv`

```csv
codigo,nombre,ean,alias
DIST-001,Enterogermina Plus Ampollas Bebibles x5 x5ml,7798389330018|7795312109017,Enterogermina Plus x5
DIST-006,Novalgina 500mg x 20 comprimidos,,Novalgina comprimidos
```

| columna  | obligatoria | para qué sirve |
|----------|-------------|----------------|
| `codigo` | no  | tu código interno, para cruzar con tu ERP |
| `nombre` | **sí** | se usa en la búsqueda por texto |
| `ean`    | no (muy recomendable) | código de barras: da el match exacto |
| `alias`  | no  | términos alternativos de búsqueda, separados por `\|` |

Acepta separador `,` o `;` (se autodetecta) y encabezados alternativos
(`producto`, `descripcion`, `gtin`, `codigo_barras`, …). El EAN se limpia de
guiones y espacios automáticamente.

**Varios EAN por producto.** No todas las cadenas cargan el mismo código para el mismo
producto: Enterogermina Plus figura como `7798389330018` en FarmaPlus y FarmaLife, pero como
`7795312109017` (el GTIN del envase secundario) en Farmacias del Pueblo. Poné todos los
códigos que conozcas separados por `|` y se prueban todos antes de caer al match por nombre.
Si un producto aparece como `NO_LISTADO` en una farmacia donde sabés que está, casi siempre
es porque esa cadena lo cargó con otro EAN: agregalo a la lista y vuelve a matchear exacto.

## Las farmacias: `farmacias.json`

```json
{ "nombre": "FarmaPlus", "tipo": "vtex", "base_url": "https://www.farmaplus.com.ar", "activa": true }
```

Verificadas y funcionando: **FarmaPlus, Farmacity, FarmaLife, Farmacias del Pueblo**.
Simplicity queda configurada pero inactiva (es perfumería, no lista medicamentos).

Opciones extra por farmacia: `"sales_channel": "2"` (canal de venta VTEX),
`"demora": 0.8` (pausa entre pedidos), `"activa": false` para saltearla.

## Cómo identifica cada producto

En orden, de más a menos confiable:

1. **EAN exacto** (`fq=alternateIds_Ean`) — sin ambigüedad.
2. **EAN como código de referencia** (`fq=alternateIds_RefId`) — algunas cadenas lo cargan ahí.
3. **Búsqueda por texto** (`ft=`) — se puntúan los candidatos y se acepta el mejor si supera
   el umbral (`--umbral`, por defecto `0.65`). Estos casos salen marcados con `revisar=SI`
   en el CSV y aparecen listados al final de la corrida.

El puntaje penaliza fuerte las diferencias de dosis y cantidad, que en farmacia cambian el
producto: `Ibuprofeno 400mg x10` contra `Ibuprofeno 600mg x20` puntúa 0.20 y se descarta.
Si durante la búsqueda por texto aparece tu EAN entre los SKUs del resultado, el match se
promueve a exacto y deja de pedir revisión.

## Salida

Cada corrida escribe dos CSV en `reportes/` (separador `;`, UTF-8 con BOM: Excel los abre bien):

- `stock-AAAAMMDD-HHMM.csv` — detalle, una fila por producto × farmacia, con precio, precio
  de lista, stock, SKU y URL del producto.
- `matriz-AAAAMMDD-HHMM.csv` — pivote para leer de un vistazo: productos en filas, farmacias
  en columnas.

Estados posibles:

| estado | significado |
|--------|-------------|
| `EN_STOCK` | el producto está publicado y con stock disponible |
| `SIN_STOCK` | está publicado pero agotado |
| `NO_LISTADO` | la farmacia no lo tiene en su catálogo |
| `ERROR` | la consulta falló (red, bloqueo); ver columna `detalle` |

## Cómo funciona por dentro

Las farmacias soportadas corren sobre **VTEX**, que expone un catálogo público en
`/api/catalog_system/pub/products/search` devolviendo precio y stock en JSON. No hace falta
parsear HTML ni levantar un navegador, así que el chequeo es rápido y no se rompe cuando
cambia el diseño del sitio.

```
check_stock.py          CLI
pharmacheck/
  catalogo.py           lectura de productos.csv
  matching.py           normalización y puntaje de nombres
  models.py             Producto, Resultado, Estado, TipoMatch
  runner.py             orquestación (una hebra por farmacia, productos en serie)
  report.py             CSV detallado, matriz y resumen en consola
  stores/
    base.py             clase base: reintentos, backoff, manejo de errores
    vtex.py             adaptador VTEX
    __init__.py         registro de adaptadores + carga de farmacias.json
test_matching.py        pruebas del matcheo por nombre
```

## Sumar una farmacia

- **Si es VTEX**: agregala a `farmacias.json` con `"tipo": "vtex"`. Para confirmarlo, abrí
  `https://SITIO/api/catalog_system/pub/products/search?ft=ibuprofeno` — si devuelve JSON, es VTEX.
- **Si no es VTEX**: creá una subclase de `AdaptadorFarmacia` en `pharmacheck/stores/`,
  implementá `chequear(producto) -> Resultado` y registrala en `ADAPTADORES`
  (`pharmacheck/stores/__init__.py`). El resto del sistema no cambia.

## Notas operativas

- Las farmacias corren en paralelo, pero los productos de cada una van en serie con una pausa
  (`--demora`, 0.4s) para no gatillar límites de rate.
- Los parámetros se codifican con `%20` en vez de `+`: el WAF de varias tiendas VTEX rechaza
  el `+` con *"Bad Request! Scripts are not allowed!"*.
- Si una tienda maneja stock por zona de entrega, configurale el `sales_channel` que
  corresponda a tu región.

```bash
python3 test_matching.py    # 22 pruebas del matcheo, la limpieza de EAN y los alias
```
