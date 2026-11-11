from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing_headers = {name.lower() for name, _ in headers}
                path = scope.get("path", "")
                admin_or_auth = path.startswith("/api/admin/") or path.startswith(
                    "/api/auth/"
                )

                for name, value in SECURITY_HEADERS.items():
                    if name.lower().encode() not in existing_headers:
                        headers.append((name.lower().encode(), value.encode()))

                if admin_or_auth:
                    headers = [
                        (name, value)
                        for name, value in headers
                        if name.lower() != b"cache-control"
                    ]
                    headers.append((b"cache-control", b"no-store"))

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
