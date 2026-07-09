import os

# The suite makes many requests from one client and shouldn't depend on Redis,
# so disable rate limiting before settings are first loaded. Rate-limit behavior
# is covered directly in test_rate_limit.py with a fake limiter.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
