# Docker log retention

Production compose uses Docker `json-file` log rotation:

```yaml
logging:
  driver: json-file
  options:
    max-size: ${DOCKER_LOG_MAX_SIZE:-50m}
    max-file: ${DOCKER_LOG_MAX_FILE:-5}
```

Forward Docker logs to Loki, Vector, Fluent Bit or another collector for centralized search and retention.
