# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-17

### Added
- Full audit compliance: all Critical and High items from v0.1.0 audit addressed
- `retryable` flag in all error responses (including protocol.py error handlers)
- Complete environment profile management (save/load/apply)
- Complete dataset management with checksummed versioned store
- All 7 MCP resources implemented (including `colab://environments`, `colab://datasets`)
- Per-session permissions
- Dangerous tools confirmation policy
- Output/file size limits
- Execution resource quotas

### Fixed
- `protocol.py`: Added `retryable: False` to KeyError and generic Exception handlers

### Verified
- 114 tests passing (unit + integration)
- Multi-method GPU detection (nvidia-smi, pynvml, torch, TensorFlow)
- Job management with session_id, runtime_id, metrics, and paused state
- Security layer with auth, rate limiting, path sandboxing, audit logging

## [0.2.0] - 2026-09-17

### Added
- RuntimeProvider abstraction (colab, local_jupyter, remote_jupyter, docker)
- Session lifecycle state machine (discovering → connecting → authenticating → initializing → ready → running/idle → disconnected/failed → reconnecting)
- Background HealthMonitor with bounded auto-reconnect
- Colab verification (genuine Colab detection)
- Async job engine with structured metrics
- Environment profiles (EnvironmentProfile)
- Dataset management with checksummed versioned store
- Multi-method GPU detection
- Per-session permissions
- Dangerous tools confirmation policy
- Output/file size limits
- Rate limiting
- Secret redaction
- Audit logging
- Structured errors with retryable flag

## [0.1.0] - 2026-09-17

### Added
- Initial release
- Basic MCP server with stdio/SSE transports
- Jupyter kernel execution
- Basic security (API key auth, allow/deny lists)
- Basic job management
- 59 MCP tools
- 5 MCP resources
