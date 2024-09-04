"""QualiCharge API utilities."""

import gzip
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


class GzipRequest(Request):
    """Handle Gzip compressed requests."""

    async def body(self) -> bytes:
        """Decompress the body beforehand."""
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            self._body = body
        return self._body


class GzipRoute(APIRoute):
    """Handle Gzip compressed requests in defined routes."""

    def get_route_handler(self) -> Callable:
        """Use the GzipRequest handler by default."""
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
