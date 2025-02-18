FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Copy the project into the image
ADD . /home/dolores
WORKDIR /home/dolores

RUN uv sync --frozen

# Place executables in the environment at the front of the path
ENV PATH="/home/dolores/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["python", "/home/dolores/src/dolores.py"]
