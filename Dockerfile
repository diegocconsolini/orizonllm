# OrizonLLM Dockerfile
# Uses Chainguard Wolfi base for enhanced security (fewer CVEs)

# Base image for building (Chainguard secure image)
ARG LITELLM_BUILD_IMAGE=cgr.dev/chainguard/wolfi-base

# Runtime image (Chainguard secure image)
ARG LITELLM_RUNTIME_IMAGE=cgr.dev/chainguard/wolfi-base

# Builder stage
FROM $LITELLM_BUILD_IMAGE AS builder

WORKDIR /app
USER root

# Install build dependencies (Alpine-based with apk)
RUN apk add --no-cache bash gcc py3-pip python3 python3-dev openssl openssl-dev

RUN python -m pip install build

# Copy the current directory contents into the container
COPY . .

# Build Admin UI
RUN chmod +x docker/build_admin_ui.sh && ./docker/build_admin_ui.sh

# Build the package
RUN rm -rf dist/* && python -m build

# There should be only one wheel file now
RUN ls -1 dist/*.whl | head -1

# Install the package
RUN pip install dist/*.whl

# Install dependencies as wheels
RUN pip wheel --no-cache-dir --wheel-dir=/wheels/ -r requirements.txt

# Ensure pyjwt is used, not jwt
RUN pip uninstall jwt -y || true
RUN pip uninstall PyJWT -y || true
RUN pip install PyJWT==2.9.0 --no-cache-dir

# Runtime stage
FROM $LITELLM_RUNTIME_IMAGE AS runtime

USER root

# Install runtime dependencies (Alpine-based with apk)
RUN apk add --no-cache bash openssl tzdata nodejs npm python3 py3-pip supervisor

WORKDIR /app

# Copy the current directory contents
COPY . .
RUN ls -la /app

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl .
COPY --from=builder /wheels/ /wheels/

# Install the built wheel using pip
RUN pip install *.whl /wheels/* --no-index --find-links=/wheels/ && rm -f *.whl && rm -rf /wheels

# Remove test files from dependencies
RUN find /usr/lib -type f -path "*/tornado/test/*" -delete 2>/dev/null || true && \
    find /usr/lib -type d -path "*/tornado/test" -delete 2>/dev/null || true

# Install semantic_router and aurelio-sdk
RUN chmod +x docker/install_auto_router.sh && ./docker/install_auto_router.sh

# Generate prisma client
RUN prisma generate
RUN chmod +x docker/entrypoint.sh
RUN chmod +x docker/prod_entrypoint.sh

EXPOSE 4000/tcp

COPY docker/supervisord.conf /etc/supervisord.conf

ENTRYPOINT ["docker/prod_entrypoint.sh"]

# Append "--detailed_debug" to the end of CMD to view detailed debug logs
CMD ["--port", "4000"]
