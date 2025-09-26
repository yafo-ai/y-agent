import json
from collections.abc import Generator
from contextlib import AbstractContextManager

import httpx
import httpx_sse
from httpx_sse import connect_sse

from src.mcp.types import ErrorData, JSONRPCError
from src.utils.encoders import jsonable_encoder

SSRF_DEFAULT_TIME_OUT = 100
SSRF_DEFAULT_CONNECT_TIME_OUT = 100
SSRF_DEFAULT_READ_TIME_OUT = 100
SSRF_DEFAULT_WRITE_TIME_OUT = 100
HTTP_REQUEST_NODE_SSL_VERIFY = False
STATUS_FORCELIST = [429, 500, 502, 503, 504]


def create_ssrf_proxy_mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
) -> httpx.Client:
    """Create an HTTPX client with SSRF proxy configuration for MCP connections.

    Args:
        headers: Optional headers to include in the client
        timeout: Optional timeout configuration

    Returns:
        Configured httpx.Client with proxy settings
    """
    return httpx.Client(
        verify=HTTP_REQUEST_NODE_SSL_VERIFY,
        headers=headers or {},
        timeout=timeout,
        follow_redirects=True,
    )


def ssrf_proxy_sse_connect(url: str, **kwargs) -> AbstractContextManager[httpx_sse.EventSource]:
    """Connect to SSE endpoint with SSRF proxy protection.

    This function creates an SSE connection using the configured proxy settings
    to prevent SSRF attacks when connecting to external endpoints. It returns
    a context manager that yields an EventSource object for SSE streaming.

    The function handles HTTP client creation and cleanup automatically, but
    also accepts a pre-configured client via kwargs.

    Args:
        url (str): The SSE endpoint URL to connect to
        **kwargs: Additional arguments passed to the SSE connection, including:
            - client (httpx.Client, optional): Pre-configured HTTP client.
              If not provided, one will be created with SSRF protection.
            - method (str, optional): HTTP method to use, defaults to "GET"
            - headers (dict, optional): HTTP headers to include in the request
            - timeout (httpx.Timeout, optional): Timeout configuration for the connection

    Returns:
        AbstractContextManager[httpx_sse.EventSource]: A context manager that yields an EventSource
        object for SSE streaming. The EventSource provides access to server-sent events.

    Example:
        ```python
        with ssrf_proxy_sse_connect(url, headers=headers) as event_source:
            for sse in event_source.iter_sse():
                print(sse.event, sse.data)
        ```

    Note:
        If a client is not provided in kwargs, one will be automatically created
        with SSRF protection based on the application's configuration. If an
        exception occurs during connection, any automatically created client
        will be cleaned up automatically.
    """

    # Extract client if provided, otherwise create one
    client = kwargs.pop("client", None)
    if client is None:
        # Create client with SSRF proxy configuration
        timeout = kwargs.pop(
            "timeout",
            httpx.Timeout(
                timeout=SSRF_DEFAULT_TIME_OUT,
                connect=SSRF_DEFAULT_CONNECT_TIME_OUT,
                read=SSRF_DEFAULT_READ_TIME_OUT,
                write=SSRF_DEFAULT_WRITE_TIME_OUT,
            ),
        )
        headers = kwargs.pop("headers", {})
        client = create_ssrf_proxy_mcp_http_client(headers=headers, timeout=timeout)
        client_provided = False
    else:
        client_provided = True

    # Extract method if provided, default to GET
    method = kwargs.pop("method", "GET")

    try:
        return connect_sse(client, method, url, **kwargs)
    except Exception:
        # If we created the client, we need to clean it up on error
        if not client_provided:
            client.close()
        raise


def create_mcp_error_response(
    request_id: int | str | None, code: int, message: str, data=None
) -> Generator[bytes, None, None]:
    """Create MCP error response"""
    error_data = ErrorData(code=code, message=message, data=data)
    json_response = JSONRPCError(
        jsonrpc="2.0",
        id=request_id or 1,
        error=error_data,
    )
    json_data = json.dumps(jsonable_encoder(json_response))
    sse_content = json_data.encode()
    yield sse_content