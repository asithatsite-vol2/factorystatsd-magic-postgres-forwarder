FROM docker.io/library/python:3.7 as builder
# Install poetry
RUN pip install poetry

WORKDIR /project

# Export locks
COPY pyproject.toml poetry.lock /project
RUN poetry export -o /tmp/requirements.txt -f requirements.txt
RUN pip wheel -r /tmp/requirements.txt -w /tmp


# Build wheel
COPY . /project
RUN poetry build --format=wheel
RUN cp dist/* /tmp


# This is the real container
FROM docker.io/library/python:3.7-slim
COPY --from=builder /tmp /tmp
RUN pip install --no-cache-dir --disable-pip-version-check /tmp/*.whl

CMD ["pg_magic_forwarder"]
