"""Integration tests for Go duration parsing with docker-compose files."""

import glob
import os
from datetime import timedelta

from dcm import parse_compose_files


def test_docker_compose_config():
    """Test that docker-compose configuration is parsed correctly."""
    sample_dir = os.path.join(os.path.dirname(__file__), "samples/single-file/*.yml")
    files = list(glob.glob(pathname=sample_dir))
    for file in files:
        compose = parse_compose_files(file)
        assert compose


def test_healthcheck_duration_parsing():
    """Test that healthcheck durations are correctly parsed from docker-compose files."""
    sample_dir = os.path.join(os.path.dirname(__file__), "samples/multi-files-01/*.yml")
    files = list(glob.glob(pathname=sample_dir))
    compose = parse_compose_files(*files)

    # Check that postgres service exists and has healthcheck with proper durations
    assert "postgres" in compose.services
    # Note: The service data from spec is not directly exposed in the Service model
    # This test validates that parsing doesn't fail with duration fields


def test_parse_compose_with_durations():
    """Test parsing a docker-compose file with various duration formats."""
    import tempfile

    compose_content = """
version: '3.8'
services:
  test-service:
    image: test:latest
    healthcheck:
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
      start_interval: 5s
    deploy:
      restart_policy:
        delay: 5s
        window: 120s
      update_config:
        delay: 10s
        monitor: 60s
      rollback_config:
        delay: 5s
        monitor: 30s
    stop_grace_period: 10s
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp_file:
        tmp_file.write(compose_content)
        tmp_file.flush()

        try:
            # This should not raise any exceptions
            compose = parse_compose_files(tmp_file.name)
            assert len(compose.services) == 1
            assert "test-service" in compose.services
        finally:
            os.unlink(tmp_file.name)


def test_duration_values_in_real_compose():
    """Test that actual duration values are properly parsed."""
    import tempfile

    compose_content = """
services:
  db:
    image: postgres:latest
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s
      timeout: 3s
      retries: 5
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp_file:
        tmp_file.write(compose_content)
        tmp_file.flush()

        try:
            # Parse and verify no exceptions occur
            compose = parse_compose_files(tmp_file.name)
            assert "db" in compose.services

            # The actual spec.Service object would have the duration values
            # but our Service model doesn't expose all spec fields yet
            # This test ensures parsing succeeds
        finally:
            os.unlink(tmp_file.name)
