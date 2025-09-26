from prometheus_client import Counter, Histogram, Gauge

# --- Metrics ---
REQUEST_LATENCY = Histogram("boe_request_latency_seconds", "Request latency per request")
USAGE = Counter("boe_articles_processed_total", "Total BOE articles processed")
ACCURACY = Gauge("boe_accuracy", "Accuracy of BOE updates")   # this one depends on your validation logic
ERRORS = Counter("boe_errors_total", "Total errors encountered in BOE processing")
PROCESSING_TIME = Histogram("boe_processing_time_seconds", "Time taken to process BOE articles")
# ---------------