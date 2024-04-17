from fastapi import Request
from fastapi.responses import HTMLResponse
from pyinstrument import Profiler
from . import ExtendedFastAPI


def register_profiling_middleware(app: ExtendedFastAPI):
    if app.settings.PROFILING_ENABLED is True:

        @app.middleware("http")
        async def profile_request(request: Request, call_next):
            """Profile the current request

            Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            with slight improvements.

            """
            profiling = request.query_params.get("profile", False)
            if profiling:
                profiler = Profiler(interval=0.001, async_mode="strict")
                profiler.start()
                await call_next(request)
                profiler.stop()
                return HTMLResponse(profiler.output_html())
            else:
                return await call_next(request)
