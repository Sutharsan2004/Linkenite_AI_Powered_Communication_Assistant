# Product Portfolio (Excerpt)
- Core Platform: Customer analytics, dashboards, role-based access.
- API: REST with OAuth2; base path /v1. Rate limit 1000 rpm.
- Regions: US, EU, APAC. EU latency may spike during regional failover windows.
- CRM Integrations: HubSpot, Salesforce (beta), Zoho (via connector).

# Troubleshooting
## Access/Dashboard
- 403 Forbidden: Usually role/permission issue or expired session token. Advise re-login, check role assignments.
- Known incident playbook: Verify status page. If outage, acknowledge and provide ETA if available.

## Billing
- Duplicate charge: Check invoice IDs and payment processor logs. Offer provisional refund and ticket escalation.

## Latency
- EU latency may increase during maintenance. Suggest retry with exponential backoff, check status page.
