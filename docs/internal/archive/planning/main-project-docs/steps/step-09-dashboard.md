# Step 09: Visual Management Dashboard

## Problem Statement

Laboratory management and staff need real-time visibility into the operational status: how many samples are pending at each stage, throughput metrics, bottlenecks, and overall productivity. Currently, this information is scattered across paper records and requires manual counting. A visual dashboard is needed to display key performance indicators (KPIs) and work-in-progress (WIP) at a glance, enabling better resource allocation and decision-making.

## Requirements

### Functional Requirements (RF09)

- **RF09.1**: WIP indicators by processing stage
- **RF09.2**: Separation between cytology and histopathology
- **RF09.3**: Volume metrics (weekly, monthly, annual)
- **RF09.4**: Real-time visualization
- **RF09.5**: Auto-update without page refresh
- Turnaround time (TAT) metrics
- Productivity per histopathologist
- Sample aging (days since reception)
- Alerts for overdue samples

### Non-Functional Requirements

- **Performance**: Dashboard loads in < 3 seconds
- **Real-time**: Updates every 30-60 seconds
- **Responsiveness**: Works on desktop and tablets
- **Clarity**: Information presented clearly with visual cues

## Data Model

### Dashboard_Metrics Table (cache table, optional)
```sql
dashboard_metrics (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  metric_name: VARCHAR(100) NOT NULL,
  metric_value: DECIMAL(10,2) NOT NULL,
  metric_date: DATE NOT NULL,
  tipo_analisis: ENUM('citologia', 'histopatologia', 'ambos'),
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY (metric_name, metric_date, tipo_analisis)
)
```

### Most Metrics Calculated from Existing Tables
- protocolo (counts by status, dates)
- informe_resultados (completion metrics)
- procesamiento_log (stage tracking)

## API Design

### Dashboard Endpoints

#### GET /api/dashboard/wip
Get work-in-progress by stage.

**Response (200 OK):**
```json
{
  "histopatologia": {
    "pendiente_recepcion": 5,
    "recibido": 3,
    "procesando": {
      "encasetado": 2,
      "fijacion": 4,
      "corte": 3,
      "coloracion": 2
    },
    "listo_diagnostico": 8,
    "diagnostico": 4,
    "informe_borrador": 2,
    "listo_envio": 3
  },
  "citologia": {
    "pendiente_recepcion": 2,
    "recibido": 1,
    "procesando": 3,
    "listo_diagnostico": 4,
    "diagnostico": 1,
    "informe_borrador": 1,
    "listo_envio": 2
  },
  "timestamp": "2024-10-15T10:30:00Z"
}
```

#### GET /api/dashboard/volume
Get volume metrics.

**Query Parameters:**
- `periodo`: 'semana', 'mes', 'año'
- `tipo`: 'citologia', 'histopatologia', 'ambos'

**Response (200 OK):**
```json
{
  "periodo": "mes",
  "fecha_desde": "2024-10-01",
  "fecha_hasta": "2024-10-31",
  "histopatologia": {
    "protocolos_recibidos": 45,
    "informes_enviados": 42,
    "promedio_dia": 1.5
  },
  "citologia": {
    "protocolos_recibidos": 28,
    "informes_enviados": 27,
    "promedio_dia": 0.9
  },
  "total": {
    "protocolos_recibidos": 73,
    "informes_enviados": 69
  }
}
```

#### GET /api/dashboard/tat
Get turnaround time metrics.

**Response (200 OK):**
```json
{
  "histopatologia": {
    "tat_promedio_dias": 7.2,
    "tat_mediana_dias": 6,
    "tat_minimo_dias": 3,
    "tat_maximo_dias": 15,
    "dentro_objetivo": 85 // % within target TAT
  },
  "citologia": {
    "tat_promedio_dias": 2.5,
    "tat_mediana_dias": 2,
    "tat_minimo_dias": 1,
    "tat_maximo_dias": 5,
    "dentro_objetivo": 95
  }
}
```

#### GET /api/dashboard/productivity
Get productivity per histopathologist.

**Query Parameters:**
- `periodo`: 'semana', 'mes', 'año'

**Response (200 OK):**
```json
{
  "periodo": "mes",
  "histopatologos": [
    {
      "nombre": "Dra. Ana López",
      "informes_enviados": 25,
      "promedio_por_semana": 6.25,
      "tat_promedio_dias": 6.8
    },
    {
      "nombre": "Dr. Juan Pérez",
      "informes_enviados": 17,
      "promedio_por_semana": 4.25,
      "tat_promedio_dias": 7.5
    }
  ],
  "total_informes": 42
}
```

#### GET /api/dashboard/aging
Get samples by age (days since reception).

**Response (200 OK):**
```json
{
  "por_rango": {
    "0-3_dias": 12,
    "4-7_dias": 18,
    "8-14_dias": 8,
    "mas_14_dias": 3
  },
  "protocolos_vencidos": [
    {
      "protocolo_numero": "HP 24/115",
      "animal": "Max - Canino",
      "dias_desde_recepcion": 16,
      "estado": "listo_diagnostico",
      "veterinario": "Dr. García"
    }
  ]
}
```

#### GET /api/dashboard/alerts
Get system alerts (overdue, bottlenecks).

**Response (200 OK):**
```json
{
  "alerts": [
    {
      "tipo": "tat_excedido",
      "severidad": "alta",
      "mensaje": "3 protocolos exceden TAT objetivo",
      "protocolos": ["HP 24/115", "HP 24/118", "CT 24/087"]
    },
    {
      "tipo": "cuello_botella",
      "severidad": "media",
      "mensaje": "8 muestras esperando diagnóstico",
      "etapa": "listo_diagnostico"
    }
  ]
}
```

## Business Logic

### WIP Calculation

**Count protocols by current status:**
```sql
SELECT 
  tipo_analisis,
  estado,
  COUNT(*) as cantidad
FROM protocolo
WHERE estado NOT IN ('enviado_informe', 'archivado')
GROUP BY tipo_analisis, estado
```

**Additional Processing Stages:**
```sql
SELECT 
  'procesando' as etapa,
  COUNT(DISTINCT p.id) as cantidad
FROM protocolo p
JOIN muestra_histopatologia m ON m.protocolo_id = p.id
JOIN cassette c ON c.muestra_histopatologia_id = m.id
WHERE c.estado = 'en_proceso'
```

### TAT Calculation

**Turnaround Time = Fecha Envío Informe - Fecha Recepción**

```sql
SELECT 
  AVG(DATEDIFF(ir.fecha_envio, p.fecha_recepcion)) as tat_promedio,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(...)) as tat_mediana,
  MIN(DATEDIFF(...)) as tat_minimo,
  MAX(DATEDIFF(...)) as tat_maximo
FROM protocolo p
JOIN informe_resultados ir ON ir.protocolo_id = p.id
WHERE ir.fecha_envio >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND p.tipo_analisis = 'histopatologia'
```

### Target TAT
- **Histopathology**: 7-10 days
- **Cytology**: 2-3 days

### Real-time Updates

**Implementation Options:**
1. **Polling**: Frontend requests every 30-60 seconds
2. **WebSockets**: Push updates when data changes
3. **Server-Sent Events (SSE)**: Server pushes updates

### Performance Optimization

**Caching Strategy:**
- Cache dashboard metrics for 5 minutes
- Invalidate cache on relevant data changes
- Use Redis/Memcached for speed
- Pre-calculate complex metrics daily

**Query Optimization:**
- Create materialized views for complex metrics
- Index on date fields and status columns
- Limit historical data queries (last 90 days)

## Acceptance Criteria

1. ✅ Dashboard displays WIP by processing stage
2. ✅ Cytology and histopathology separated
3. ✅ Volume metrics for week/month/year
4. ✅ TAT metrics calculated correctly
5. ✅ Productivity per histopathologist shown
6. ✅ Sample aging displayed with alerts
7. ✅ Dashboard updates automatically
8. ✅ Loads in < 3 seconds
9. ✅ Responsive design for desktop/tablet
10. ✅ Visual cues for alerts (colors, icons)

## Testing Approach

### Unit Tests
- WIP calculation logic
- TAT calculation logic
- Productivity calculation
- Aging bucket logic

### Integration Tests
- Dashboard API returns correct data
- Real-time update mechanism
- Cache invalidation
- Query performance

### E2E Tests
- Dashboard loads with all widgets
- Data refreshes automatically
- Click through to protocol details
- Alerts display correctly

### Performance Tests
- Load dashboard with 1 year of data
- Concurrent access (10+ users)
- Real-time update performance
- Cache hit rate

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Real-time Update Method**:
   - Polling (simple, works everywhere)
   - WebSockets (efficient, bidirectional)
   - SSE (server push, simpler than WebSockets)

2. **Charting Library**:
   - Chart.js (simple, good for basics)
   - D3.js (powerful, flexible)
   - Recharts (React specific)
   - ApexCharts (modern, feature-rich)

3. **Caching Strategy**:
   - Application cache (simple)
   - Redis (performant)
   - Database materialized views

### Dashboard Layout

**Proposed Layout:**
```
┌─────────────────────────────────────────────────┐
│                    HEADER                       │
│  Laboratorio de Anatomía Patológica - Dashboard│
└─────────────────────────────────────────────────┘
┌───────────────┬─────────────────────────────────┐
│   WIP         │     VOLUME METRICS              │
│   Histogram   │     Charts (Week/Month/Year)    │
│   by Stage    │                                 │
├───────────────┼─────────────────────────────────┤
│   TAT         │     PRODUCTIVITY                │
│   Metrics     │     Per Histopathologist        │
├───────────────┴─────────────────────────────────┤
│   ALERTS & AGING                                │
│   Overdue samples, Bottlenecks                  │
└─────────────────────────────────────────────────┘
```

## Dependencies

### Must be completed first:
- Step 03: Protocol Submission
- Step 04: Sample Reception
- Step 05: Sample Processing
- Step 06: Report Generation

### Estimated Effort

**Time**: 1 week (Sprint 12-13)

**Breakdown**:
- Backend metrics API: 2 days
- Frontend dashboard layout: 2 days
- Charts and visualizations: 1.5 days
- Real-time updates: 1 day
- Testing: 0.5 days

## Implementation Notes

### Sample WIP Widget (React Example)
```jsx
function WIPWidget({ data }) {
  return (
    <div className="wip-widget">
      <h2>Work In Progress - Histopatología</h2>
      <div className="stages">
        <Stage name="Pendiente Recepción" count={data.pendiente_recepcion} color="blue" />
        <Stage name="Procesando" count={data.procesando.total} color="yellow" />
        <Stage name="Listo Diagnóstico" count={data.listo_diagnostico} color="orange" />
        <Stage name="Diagnóstico" count={data.diagnostico} color="purple" />
        <Stage name="Listo Envío" count={data.listo_envio} color="green" />
      </div>
    </div>
  );
}
```

### Auto-refresh Logic
```javascript
useEffect(() => {
  const fetchDashboard = async () => {
    const data = await api.get('/dashboard/wip');
    setDashboardData(data);
  };
  
  fetchDashboard(); // Initial load
  const interval = setInterval(fetchDashboard, 60000); // Every minute
  
  return () => clearInterval(interval);
}, []);
```

### Testing Checklist
- [ ] WIP widget displays correct counts
- [ ] Volume charts show historical trends
- [ ] TAT metrics calculate correctly
- [ ] Productivity per pathologist accurate
- [ ] Aging alerts show overdue samples
- [ ] Dashboard auto-refreshes
- [ ] Loads quickly with real data
- [ ] Responsive on different screen sizes

