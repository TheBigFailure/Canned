from capi import *


class StandardResponse:
    NotFound: HttpResponse = HttpResponse(status=404, reason="Not Found")
    OK: HttpResponse = HttpResponse(status=200, reason="OK")
    class MethodNotAllowed(HttpResponse):
        def __init__(self, reason: str = "Method Not Allowed.", expected_methods: set[str] = None):
            super().__init__(status=405, reason=f"{reason} Expected methods: {', '.join(expected_methods)}")
    # MethodNotAllowed: HttpResponse = HttpResponse(status=405, reason="Method Not Allowed")

    class Unauthorised(HttpResponse):
        def __init__(self, reason: str = "Unauthorised user"):
            super().__init__(status=401, reason=reason)



