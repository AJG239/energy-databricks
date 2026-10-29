# Exploración de la API REData de REE

> Resultado de la fase 1 (exploración) del proyecto. Fecha: 2026-10-29.
> Documentación oficial: https://www.ree.es/es/apidatos

## 1. Formato de las peticiones

```
GET https://apidatos.ree.es/{lang}/datos/{category}/{widget}?start_date=...&end_date=...&time_trunc=...
```

| Parámetro | Valores |
|---|---|
| `lang` | `es` / `en` |
| `start_date`, `end_date` | ISO 8601 `YYYY-MM-DDTHH:MM` |
| `time_trunc` | `hour`, `day`, `month`, `year` |
| `geo_trunc`, `geo_limit`, `geo_ids` | Opcionales, **los tres juntos o ninguno**. Peninsular: `electric_system` / `peninsular` / `8741` |

- Sin token.
- ⚠️ La API es `apidatos.ree.es`. `www.ree.es` es la web y devuelve HTML (provoca `JSONDecodeError`).

## 2. Estructura de la respuesta

```
data        → metadatos del widget (type, id, title, last-update)
included    → lista de indicadores (series)
  └── attributes
        ├── title, type (Renovable / No-Renovable / total), last-update
        └── values → lista de {value, percentage, datetime}
```

- `percentage` es el reparto para el gráfico de la web: **sin valor de negocio, se descarta**.
- `last-update` puede ser **meses posterior** al dato: REE revisa datos históricos, así que la ingesta debe poder volver a descargar periodos pasados sin duplicar.
- `magnitude` suele venir vacío: las unidades se documentan aquí.

## 3. Widgets explorados

| Widget | `time_trunc` | Indicadores | Granularidad y unidades |
|---|---|---|---|
| `mercados/precios-mercados-tiempo-real` | `hour` ✅ | 2: `PVPC` (1001) y `Precio mercado spot` (600) | PVPC horario (24/día); spot cada **15 min** (96/día). €/MWh |
| `demanda/evolucion` | `hour` ✅ | 1: `Demanda` (10297) | Horaria, **MW**. 01/10/2025 peninsular ≈ 637 GWh/día |
| `generacion/estructura-generacion` | `hour` ❌ (400) · `day` ✅ | 16: 15 tecnologías + `Generación total` (10296) | Diaria, **MWh**. No sumar `Generación total` con el resto |

## 4. Tiempo y cambio de hora

- `datetime` viene en hora local con desfase: `+02:00` (CEST, verano) o `+01:00` (CET, invierno).
- **2025-10-26 → 25 valores**: la 02:00 aparece con `+02:00` y otra vez con `+01:00`.
- **2025-03-30 → 23 valores**: de `01:00+01:00` se pasa a `03:00+02:00`.
- Conclusión: la hora local sola es ambigua o inexistente esos días. Se guardará en **UTC** a partir del desfase.

## 5. Límites y errores

- Con `time_trunc=hour`: **máximo 30 días por petición** (30 días funciona, 31 falla; cruzar de mes no influye). Pendiente: comprobar el límite con `day`.
- Errores: código 400 con cuerpo `{"errors": [{"status", "title", "detail"}]}`. Un `time_trunc` no válido o no soportado por el widget da 400.
- ⚠️ El `detail` puede engañar: el 400 de generación con `hour` dice "inténtelo de nuevo más tarde", pero reintentar no lo arregla.
- Pendiente: widget inexistente, fecha mal escrita y rango de más de 30 días.

## 6. Consecuencias para el diseño

1. **Ingesta guiada por configuración**: un catálogo de widgets (categoría, widget, `time_trunc`, ámbito geográfico, días máximos por petición) y una única función de descarga.
2. **Troceo del rango**: el backfill se parte en tramos de como mucho 30 días.
3. **Reintentos**: solo para errores transitorios (timeouts, 429, 5xx). Fallo inmediato en 4xx, guardando el `detail` en el log.
4. **UTC** en silver; clave natural = indicador + timestamp UTC.
5. **Ámbito geográfico único**: peninsular para todos los widgets.
6. La generación por tecnología solo existe por días: irá en `agg_diario`, no en la tabla horaria.
7. Re-descarga de periodos recientes para recoger las revisiones de REE, sin duplicar (idempotencia).
