"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Gauge, Histogram

# Webhook metrics
webhook_updates_total = Counter(
    "telegram_webhook_updates_total", "Total number of webhook updates received", ["update_type"]
)

# Profile metrics
profiles_created_total = Counter("profiles_created_total", "Total number of profiles created")

profiles_edited_total = Counter("profiles_edited_total", "Total number of profile edits")

# Match metrics
match_requests_total = Counter("match_requests_total", "Total number of match requests")

matches_created_total = Counter("matches_created_total", "Total number of successful matches", ["status"])

# Active users
active_users = Gauge("active_users", "Number of active users in the system")

# Queue metrics
match_queue_size = Gauge("match_queue_size", "Current size of match queue")

# Response time metrics
api_request_duration = Histogram(
    "api_request_duration_seconds", "API request duration in seconds", ["method", "endpoint", "status"]
)

bot_handler_duration = Histogram("bot_handler_duration_seconds", "Bot handler duration in seconds", ["handler"])

# Payment metrics
tips_created_total = Counter("tips_created_total", "Total number of tips created", ["currency", "status"])

tips_amount_total = Counter("tips_amount_total", "Total amount of tips in minor units", ["currency"])

tips_paid_total = Counter("tips_paid_total", "Total number of tips successfully paid")

tips_errors_total = Counter("tips_errors_total", "Total number of tip errors", ["error_type"])

tips_processing_duration = Histogram(
    "tips_processing_duration_seconds", "Time to process tip payment from callback to invoice creation"
)

# AI coach metrics
ai_hints_generated_total = Counter("ai_hints_generated_total", "Total number of AI hints generated", ["hint_type"])

ai_hints_accepted_total = Counter(
    "ai_hints_accepted_total", "Total number of AI hints accepted by users", ["hint_type"]
)

safety_flags_total = Counter("safety_flags_total", "Total number of safety flags raised", ["label", "severity"])

# Sprint 5: Safety & Moderation metrics
reports_total = Counter("reports_total", "Total number of reports created", ["reason"])

reports_latency_seconds = Histogram(
    "reports_latency_seconds", "Time to process report creation from request to response"
)

blocks_total = Counter("blocks_total", "Total number of user blocks executed")

blocks_latency_seconds = Histogram("blocks_latency_seconds", "Time to process block action from request to response")
