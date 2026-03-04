# Monitoring Configuration

## Overview

The laboratory system uses Sentry for comprehensive monitoring, including error tracking, performance monitoring, and log aggregation. This provides visibility into system health and performance issues.

## Current Implementation

### ✅ Sentry Integration (Active)

**Configuration Location**: `src/config/settings.py:54-71`

**Features Enabled**:
- **Error Tracking**: All exceptions and errors automatically sent to Sentry
- **Performance Monitoring**: Request traces with 10% sample rate in development, 100% in production
- **Profiling**: Sampled profiling data collection (disabled in dev, enabled in production)
- **PII Tracking**: Personally identifiable information sent for better debugging
- **Environment Tagging**: Development/production environment separation

**Environment Variables**:
```bash
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development  # or production
SENTRY_TRACES_SAMPLE_RATE=0.1   # 10% in dev, 1.0 in prod
SENTRY_PROFILES_SAMPLE_RATE=0.0 # Disabled in dev, 1.0 in prod
```

### Accessing Sentry

1. **Debug Endpoint**: `/sentry-debug/` - Triggers an error for testing
2. **Dashboard**: Access your Sentry project dashboard for:
   - Error overview and trends
   - Performance traces
   - User sessions with errors
   - Release tracking

### What Sentry Currently Captures

#### Errors & Exceptions
- All unhandled exceptions
- Custom error reports
- JavaScript errors (if configured in frontend)
- 404 and 5xx server errors

#### Performance Data
- Request/response times
- Database query performance
- External API calls
- Celery task execution

#### Context Information
- User ID and email (when authenticated)
- Request headers and parameters
- Release version
- Environment (dev/prod)

## Missing Components

### ❌ Custom Metrics

While Sentry captures performance traces, custom business metrics are not yet implemented:

**Potential Metrics to Add**:
- Protocol submission rates
- Report generation times
- Email delivery success rates
- User login patterns
- Sample processing throughput

**Implementation Options**:
```python
# Using Sentry custom metrics
from sentry_sdk import set_measurement

# Example: Track protocol submission time
with sentry_sdk.configure_scope() as scope:
    scope.set_tag("protocol_type", "histopathology")
    set_measurement("protocol_submission_time", duration, "second")
```

### ❌ Dashboard Integration

No custom dashboards within the application for displaying metrics. Consider adding:
- Real-time metrics sidebar
- Health check page
- Admin panel with key metrics

## Recommended Next Steps

### 1. Set Up Alerts
```python
# In Sentry dashboard, configure alerts for:
- Error rate spikes
- Performance degradation
- New issue patterns
```

### 2. Add Custom Metrics
```python
# Track important business KPIs
def track_protocol_submission(protocol):
    sentry_sdk.add_breadcrumb(
        category='protocol',
        message=f'Protocol {protocol.temporary_code} submitted',
        level='info',
        data={
            'protocol_type': protocol.get_protocol_type(),
            'veterinarian_id': protocol.veterinarian_id,
        }
    )
```

### 3. Performance Optimization
- Use Sentry profiling data to identify bottlenecks
- Monitor database query performance
- Track Celery task execution times

### 4. Log Integration
- Ensure all important actions create breadcrumbs
- Add context for better debugging
- Track user flows through the system

## Security Considerations

- **PII is enabled** - Ensure Sentry DSN is properly secured
- Review what data is sent to Sentry
- Consider data retention policies
- Use source maps for frontend errors

## Monitoring Best Practices

1. **Review Sentry regularly** - Check for new errors weekly
2. **Set up meaningful alerts** - Avoid alert fatigue
3. **Add context to errors** - Include relevant business context
4. **Track releases** - Mark deployments to correlate errors
5. **Monitor performance trends** - Watch for degradation over time

## Conclusion

Sentry provides excellent coverage for error tracking and performance monitoring. The system is well-monitored for operational issues. The main gap is custom business metrics, which can be added as needed based on business priorities.

**Status**: ✅ Core monitoring functional with Sentry