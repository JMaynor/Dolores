FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Copy the project into the image
ADD . /home/dolores
WORKDIR /home/dolores

RUN uv sync --frozen

# Place executables in the environment at the front of the path
ENV PATH="/home/dolores/.venv/bin:$PATH"

# Set PYTHONPATH to include the top-level project folder
ENV PYTHONPATH="/home/dolores"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["python", "/home/dolores/src/main.py"]
