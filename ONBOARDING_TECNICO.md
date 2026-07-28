# Onboarding técnico ILTONIF — procedimiento repetible

Cómo conectar la tienda de un cliente nuevo al pipeline diario sin trabajo artesanal. Dos rutas según la plataforma del cliente: **Shopify** (automática) o **CSV** (semanal, para cualquier otra plataforma).

Antes de esto ya debe estar hecha la auditoría gratuita (`auditoria/auditoria.py`) y el piloto aceptado. Este documento empieza cuando el cliente dice que sí.

---

## Ruta A — Cliente con Shopify (preferente)

Tiempo estimado: 15-20 min, la mayor parte esperando a que el cliente genere el token.

### A1. Pedir al cliente un token de solo lectura

Enviarle estas instrucciones tal cual (no necesita saber nada técnico):

> En tu panel de Shopify: **Configuración → Aplicaciones y canales de venta → Desarrollar aplicaciones → Crear una aplicación**.
> Nómbrala "ILTONIF" y, en **Configurar los ámbitos de la API de Admin**, marca solo estos permisos de lectura:
> - `read_products`
> - `read_inventory`
> - `read_orders`
>
> Guarda, pulsa **Instalar aplicación** y cópiame el *Admin API access token* (empieza por `shpat_`).

Dos datos a recibir: el dominio de la tienda (`nombre.myshopify.com`) y el token.

**Importante:** solo lectura. ILTONIF nunca necesita permisos de escritura — decirlo explícitamente al cliente, reduce fricción.

### A2. Cargar las credenciales

En GitHub, repo `iltonifsaas/iltonif-dashboard` → **Settings → Secrets and variables → Actions**:

- `SHOPIFY_STORE` = `nombre.myshopify.com`
- `SHOPIFY_TOKEN` = el token `shpat_...`

### A3. Probar la ingesta antes de dejarla automática

En la pestaña **Actions → Actualizar dataset diario → Run workflow**, lanzarlo a mano. Comprobar en el log que:

- La lista de productos se descarga sin errores 401/403 (si falla, el token no tiene los ámbitos correctos).
- Aparece un commit nuevo `data: dataset actualizado ... [pipeline]`.
- El número de SKUs cuadra aproximadamente con el catálogo real del cliente.

A partir de aquí corre solo cada día a las 05:00 UTC (07:00 Madrid en verano).

### A4. Verificar el dashboard

Abrir la app y comprobar que aparecen los productos del cliente, con stock y precio coherentes. El workflow de warm-up despierta la app automáticamente tras cada push.

---

## Ruta B — Cliente sin Shopify (CSV semanal)

Para WooCommerce, PrestaShop, OpenCart, plataforma propia, etc. Es la ruta de la mayoría de prospectos actuales del CRM.

### B1. Pedir dos CSV

El cliente exporta desde su plataforma:

**Ventas** — una fila por producto y día (o por pedido):

| fecha | sku | unidades |
|---|---|---|
| 2026-04-05 | PX-P001 | 5 |

**Stock** — una fila por producto, foto del momento:

| sku | nombre | stock | precio | coste (opcional) |
|---|---|---|---|---|
| PX-P001 | Pienso Royal Canin Medium Adult 15kg | 18 | 62.90 | 37.50 |

**No hace falta que las columnas se llamen exactamente así.** El pipeline reconoce automáticamente los nombres habituales en español, inglés y de exportación Shopify:

- fecha: `fecha`, `date`, `created_at`, `dia`, `fecha_pedido`, `order_date`
- sku: `sku`, `referencia`, `ref`, `codigo`, `ean`, `variant_sku`, `product_id`
- unidades: `unidades`, `cantidad`, `qty`, `quantity`, `net_quantity`, `uds`, `ventas`
- nombre: `nombre`, `producto`, `title`, `product_title`, `descripcion`
- stock: `stock`, `inventario`, `existencias`, `available`, `inventory_quantity`
- precio: `precio`, `price`, `pvp`, `precio_venta`, `variant_price`
- coste: `coste`, `cost`, `coste_unitario`, `cost_per_item`

Fechas: acepta tanto ISO (`2026-04-05`) como formato español (`05/04/2026`) — lo detecta solo.

Si falta el coste, la herramienta asume un 60% del PVP y lo declara explícitamente en el informe.

### B2. Guardar y ejecutar

Guardar los CSV en una carpeta por cliente y lanzar:

```
python3 auditoria/auditoria.py --ventas ventas.csv --stock stock.csv --tienda "Nombre de la tienda"
```

Si falta alguna columna obligatoria, el script no adivina: dice exactamente qué falta y qué nombres acepta. Pedirle al cliente el export corregido en vez de editarlo a mano (que sea repetible es justo el objetivo).

### B3. Cadencia

Acordar con el cliente un día fijo de envío semanal (recomendado: lunes por la mañana). Anotar la próxima fecha esperada en el CRM como próxima acción, para que no se pierda.

---

## Checklist de onboarding (copiar por cliente)

- [ ] Auditoría gratuita entregada y piloto aceptado
- [ ] Plataforma identificada (Shopify → ruta A / otra → ruta B)
- [ ] Credenciales o primer CSV recibidos
- [ ] Primera ingesta ejecutada y verificada en el log
- [ ] Datos del cliente visibles en el dashboard, con cifras coherentes
- [ ] Sesión de kickoff agendada (criterio de éxito: ahorro identificado ≥ 3x la suscripción mensual)
- [ ] Cadencia acordada (automática en Shopify / día fijo semanal en CSV)
- [ ] Cliente registrado en el CRM con etapa "Piloto" y próxima acción con fecha

---

## Limitaciones conocidas (a resolver antes de escalar)

- **Multi-tenant pendiente.** Hoy el despliegue tiene un único dataset y contraseña compartida. Con más de un piloto simultáneo hace falta el login por cuenta (`st.login()`/`st.user` de Streamlit) que ya está planificado en Asana — hacerlo antes de que arranquen los pilotos en paralelo, no después.
- **Precios de competencia.** El pipeline lee `data/competitor_prices.csv` si existe; si no, arrastra los últimos conocidos. La integración real (Google Shopping vía SerpAPI/DataForSEO, emparejando por EAN) está pendiente. Pedir a cada piloto sus 3-5 competidores reales para acotar coste.
- **Las columnas de competencia del pipeline principal siguen con nombres del dataset original** (`precio_decathlon`, `precio_trailzone`, `precio_outdoorpro`). Funciona, pero conviene renombrarlas a algo genérico (`precio_comp_1/2/3`) cuando se conecte la fuente real, para que no confunda.
