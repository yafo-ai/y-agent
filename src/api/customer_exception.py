
from uuid import uuid4
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from src.utils.log_helper import logger
from src.database.db_session import current_request_id,on_request_end


class NoPermissionException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
    def __repr__(self):
        return f"<{self.__class__.__name__} detail={self.detail }>"

class ValidationException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
    def __repr__(self):
        return f"<{self.__class__.__name__} detail={self.detail }>"

class BusinessException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
    def __repr__(self):
        return f"<{self.__class__.__name__} detail={self.detail }>"

class NotFoundException(Exception):
    
    def __init__(self, detail: str):
        self.detail = detail
    def __repr__(self):
        return f"<{self.__class__.__name__} detail={self.detail }>"
    

def register_middleware(app):
    @app.middleware("http")
    def add_request_id_header(request: Request, call_next):
        current_request_id.set(uuid4().hex)
        response = call_next(request)
        on_request_end()
        return response



def register_exception(app):
    
    @app.exception_handler(NoPermissionException)
    def noPermission_exception_handler(request: Request, exc: NoPermissionException):
        logger.error(f"{repr(exc)}")
        return JSONResponse(
            status_code=415,
            content={"detail": f"{exc.detail}" },
        )

    @app.exception_handler(ValidationException)
    def validation_exception_handler(request: Request, exc: ValidationException):
        logger.error(f"{repr(exc)}")
        return JSONResponse(
            status_code=422,
            content={"detail": f"{exc.detail}" },
        )


    @app.exception_handler(BusinessException)
    def business_exception_handler(request, exc):
        logger.error(f"{repr(exc)}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"{exc.detail}" },
        )
    
    @app.exception_handler(NotFoundException)
    def notFound_exception_handler(request, exc):
        logger.error(f"{repr(exc)}")
        return JSONResponse(
            status_code=404,
            content={"detail": f"{exc.detail}" },
        )

    @app.exception_handler(Exception)
    def exception_exception_handler(request, exc):
        logger.error(f"{repr(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"{exc}" },
        )
