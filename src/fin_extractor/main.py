"""Server entrypoint for Financial PDF Extractor API."""

import uvicorn


def run():
    """Starts the Uvicorn ASGI server."""
    uvicorn.run(
        "fin_extractor.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
