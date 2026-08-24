FROM python:3.13@sha256:a922e65d7cd72025d709fe78f3847c4cf89cc69c6fe1b6902f1c4d39fe9af82e AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

# dont use dev deps from pyproject.toml
ENV UV_NO_DEV=1

COPY uv.lock pyproject.toml /app/
COPY src /app/src
RUN uv sync --locked
# to not rebuild lockfile during venv setup

FROM python:3.13@sha256:a922e65d7cd72025d709fe78f3847c4cf89cc69c6fe1b6902f1c4d39fe9af82e AS runtime

RUN useradd -m appuser
WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
COPY --from=build /app/pyproject.toml /app/

ENV PATH="/app/.venv/bin:$PATH"

# The code defaults to 127.0.0.1 so a bare local run is not exposed. Inside a container
# that would bind container loopback only and be unreachable, so the image carries the
# container-appropriate default. Exposure is governed by port publishing, not this.
ENV API_HOST=0.0.0.0
# Metadata only — publishes and forwards nothing. Documents the default port; the actual
# container port comes from API_PORT at runtime.
EXPOSE 8000

RUN chown -R appuser:appuser /app

USER appuser

# fixed command: always runs the app module
ENTRYPOINT ["python", "-m", "app.main"]
# default args (empty); overridden by docker run args (e.g. --sets MH3 --force)
CMD []
