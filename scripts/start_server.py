"""Start the FastAPI server."""

import uvicorn

if __name__ == "__main__":
    # Use import string format to enable reload
    uvicorn.run(
        "sputnik.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

