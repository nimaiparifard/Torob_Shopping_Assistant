"""
Main FastAPI application for Torob AI Assistant
"""

import os
import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse
from .exceptions import (
    TorobAPIException, RouterNotInitializedException, AgentNotAvailableException,
    InvalidMessageTypeException, EmptyQueryException, ProcessingErrorException
)
from .validators import (
    validate_message_type, validate_text_content, validate_image_content,
    validate_chat_id, validate_random_keys, sanitize_response_message
)
from .logging_config import setup_logging, log_http_request, log_chat_interaction
from .session_manager import cleanup_sessions
from router import Router
from response_format import Response

# Configure enhanced logging
setup_logging()
logger = logging.getLogger(__name__)

# Global variables for router
router: Optional[Router] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    # Startup
    logger.info("Starting Torob AI Assistant API...")
    await initialize_services()
    logger.info("API startup complete!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Torob AI Assistant API...")
    await cleanup_services()
    logger.info("API shutdown complete!")


async def initialize_services():
    """Initialize all services and agents"""
    global router
    
    try:
        # Initialize router with existing configuration
        router = Router()
        
        logger.info("All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def cleanup_services():
    """Cleanup all services and close connections"""
    global router
    
    try:
        if router:
            router.close()
            router = None
            logger.info("Router cleaned up successfully!")
        
        # Cleanup HTTP sessions
        await cleanup_sessions()
        logger.info("HTTP sessions cleaned up successfully!")
        
        logger.info("All services cleaned up successfully!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def get_router() -> Router:
    """Dependency to get router instance"""
    if router is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    return router


# Create FastAPI app
app = FastAPI(
    title="Torob AI Assistant API",
    description="AI-powered shopping assistant for Torob platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests, especially POST requests"""
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Log request details
    logger.info(f"Request started: {request.method} {request.url.path}")
    logger.info(f"Client IP: {client_ip}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # For POST requests, log the body
    body_content = None
    if request.method == "POST":
        try:
            # Read the request body
            body = await request.body()
            if body:
                # Try to parse as JSON for better logging
                try:
                    body_json = json.loads(body.decode())
                    body_content = json.dumps(body_json, indent=2, ensure_ascii=False)
                    logger.info(f"POST Body (JSON): {body_content}")
                except json.JSONDecodeError:
                    # If not JSON, log as text
                    body_content = body.decode()
                    logger.info(f"POST Body (Text): {body_content}")
            else:
                logger.info("POST Body: (empty)")
        except Exception as e:
            logger.warning(f"Could not read POST body: {e}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response details
    logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    # Log response content for POST requests
    response_content = None
    if request.method == "POST" and response.status_code == 200:
        try:
            # Get response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Try to parse as JSON
            try:
                response_json = json.loads(response_body.decode())
                response_content = json.dumps(response_json, indent=2, ensure_ascii=False)
                logger.info(f"POST Response (JSON): {response_content}")
            except json.JSONDecodeError:
                response_content = response_body.decode()
                logger.info(f"POST Response (Text): {response_content}")
            
            # Create a new response with the body content
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                content=response_json if 'response_json' in locals() else response_body.decode(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            logger.warning(f"Could not read response body: {e}")
    
    # Use enhanced logging for HTTP requests
    log_http_request(
        method=request.method,
        path=request.url.path,
        client_ip=client_ip,
        status_code=response.status_code,
        process_time=process_time,
        body=body_content,
        headers=dict(request.headers),
        response=response_content
    )
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Torob AI Assistant API is running",
        version="1.0.0"
    )


@app.get("/system/status")
async def system_status():
    """System status endpoint to monitor file descriptors and connections"""
    import psutil
    
    try:
        current_process = psutil.Process()
        
        # Get file descriptor information
        open_files = len(current_process.open_files())
        connections = len(current_process.connections())
        
        # Get memory usage
        memory_info = current_process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Get CPU usage
        cpu_percent = current_process.cpu_percent()
        
        return {
            "status": "healthy",
            "file_descriptors": {
                "open_files": open_files,
                "connections": connections,
                "total_fds": open_files + connections
            },
            "memory": {
                "rss_mb": round(memory_mb, 2),
                "percent": current_process.memory_percent()
            },
            "cpu_percent": cpu_percent,
            "threads": current_process.num_threads(),
            "recommendations": {
                "max_recommended_fds": 1000,
                "warning_threshold": 800,
                "critical_threshold": 950
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Could not retrieve system status"
        }


@app.get("/download/logs")
async def download_logs():
    """Download all log files as a zip archive"""
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    def create_zip():
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            log_files = [
                'logs/api.log',
                'logs/http_requests.log', 
                'logs/chat_interactions.log',
                'logs/errors.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    # Read file in chunks to handle large files
                    with open(log_file, 'rb') as f:
                        zip_file.writestr(os.path.basename(log_file), f.read())
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def iter_zip():
        zip_buffer = create_zip()
        while chunk := zip_buffer.read(8192):  # Read in 8KB chunks
            yield chunk
    
    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=torob_logs.zip"}
    )


@app.get("/download/logs/{log_type}")
async def download_specific_log(log_type: str):
    """Download a specific log file"""
    from fastapi.responses import StreamingResponse
    
    # Define allowed log types
    allowed_logs = {
        'api': 'logs/api.log',
        'http': 'logs/http_requests.log',
        'chat': 'logs/chat_interactions.log', 
        'errors': 'logs/errors.log'
    }
    
    if log_type not in allowed_logs:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid log type. Allowed types: {list(allowed_logs.keys())}"
        )
    
    log_file_path = allowed_logs[log_type]
    
    if not os.path.exists(log_file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Log file '{log_type}' not found"
        )
    
    def iter_file():
        with open(log_file_path, 'rb') as f:
            while chunk := f.read(8192):  # Read in 8KB chunks
                yield chunk
    
    return StreamingResponse(
        iter_file(),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=torob_{log_type}_log.log"}
    )


@app.get("/logs/list")
async def list_logs():
    """List available log files and their sizes"""
    
    log_files = {
        'api': 'logs/api.log',
        'http': 'logs/http_requests.log',
        'chat': 'logs/chat_interactions.log',
        'errors': 'logs/errors.log'
    }
    
    result = {}
    
    for log_type, file_path in log_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            result[log_type] = {
                'file_path': file_path,
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'download_url': f"/download/logs/{log_type}"
            }
        else:
            result[log_type] = {
                'file_path': file_path,
                'size_bytes': 0,
                'size_mb': 0,
                'download_url': f"/download/logs/{log_type}",
                'status': 'not_found'
            }
    
    return result


@app.get("/download")
async def download_page():
    """Serve the download page"""
    return FileResponse("download_logs.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    router_instance: Router = Depends(get_router)
):
    """
    Main chat endpoint for user interactions
    
    This endpoint processes user messages and returns appropriate responses
    with product recommendations and random keys.
    """
    logger.info(f"Chat request received - Chat ID: {request.chat_id}, Messages count: {len(request.messages)}")
    chat_start_time = time.time()
    
    try:
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Validate chat ID
        if not validate_chat_id(request.chat_id):
            raise HTTPException(status_code=400, detail="Invalid chat ID format")
        
        # Process all messages to extract text and image content
        user_query = ""
        image_query = None
        
        logger.info(f"Processing {len(request.messages)} messages")
        
        for i, message in enumerate(request.messages):
            logger.info(f"Message {i+1}: type={message.type}, content_length={len(message.content)}")
            
            # Validate message type
            validate_message_type(message.type)
            
            if message.type == "text":
                # Extract text content and append to user query
                text_content = validate_text_content(message.content)
                if user_query:
                    user_query += " " + text_content
                else:
                    user_query = text_content
                    
                # Check if text contains image URL pattern @https://
                import re
                image_url_pattern = r'@(https?://[^\s]+)'
                image_matches = re.findall(image_url_pattern, message.content)
                if image_matches:
                    # Use the first image URL found
                    image_query = image_matches[0]
                    logger.info(f"Found image URL in text: {image_query}")
                    
            elif message.type == "image":
                # Handle image content - could be base64 data URL or regular URL
                image_content = message.content.strip()
                
                # Check if it's a base64 data URL
                if image_content.startswith('data:image/'):
                    # Extract base64 data from data URL
                    try:
                        # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...
                        header, base64_data = image_content.split(',', 1)
                        image_query = base64_data
                        logger.info(f"Found base64 image data: {len(base64_data)} characters")
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid base64 image format")
                elif image_content.startswith(('http://', 'https://')):
                    # Handle URL format
                    image_query = image_content
                    logger.info(f"Found image URL: {image_query}")
                else:
                    # Assume it's raw base64 data without data URL prefix
                    image_query = image_content
                    logger.info(f"Found raw base64 image data: {len(image_content)} characters")
        
        # Ensure we have at least some text content
        if not user_query.strip():
            user_query = "تصویر"  # Default text for image-only requests
            
        logger.info(f"Final query: '{user_query}', Image: {image_query is not None}")
        
        # Process the query through the existing router
        response = await router_instance.route(request.chat_id, user_query, image_query)

        # Convert Response object to ChatResponse format
        response_message = response.message
        base_random_keys = response.base_random_keys
        member_random_keys = response.member_random_keys

        logger.info(f"Router response - message: {repr(response_message)}, base_keys: {base_random_keys}, member_keys: {member_random_keys}")
        
        # Handle null message case first - return None for JSON null
        if response_message is None or response_message == "null":
            response_message = None
        else:
            response_message = sanitize_response_message(response_message)
        
        base_random_keys = validate_random_keys(base_random_keys, max_count=200)
        member_random_keys = validate_random_keys(member_random_keys, max_count=200)
        
        # Log response details
        logger.info(f"Chat response prepared - Message: {repr(response_message)}, Keys count: {len(base_random_keys or [])}")
        
        # Calculate total processing time
        total_process_time = time.time() - chat_start_time
        
        # Use enhanced chat logging
        log_chat_interaction(
            chat_id=request.chat_id,
            user_query=user_query,
            agent_type="ROUTER",  # Since we're using the router directly
            response_message=response_message,
            keys_count=len(base_random_keys or []),
            process_time=total_process_time
        )
        
        # Create and return the response
        chat_response = ChatResponse(
            message=response_message,
            base_random_keys=base_random_keys,
            member_random_keys=member_random_keys
        )
        
        logger.info(f"Returning ChatResponse - message: {repr(chat_response.message)}")
        return chat_response
        
    except HTTPException:
        raise
    except TorobAPIException as e:
        logger.error(f"Torob API error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error processing chat request: {e}")
        # Only return error message for actual processing errors, not for null responses
        if "null" in str(e).lower() or "none" in str(e).lower():
            return ChatResponse(
                message="خطایی در پردازش درخواست شما رخ داده است. لطفا دوباره تلاش کنید.",
                base_random_keys=None,
                member_random_keys=None
            )
        else:
            return ChatResponse(
                message="متأسفم، خطایی در پردازش درخواست شما رخ داده است. لطفا دوباره تلاش کنید.",
                base_random_keys=None,
                member_random_keys=None
            )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
