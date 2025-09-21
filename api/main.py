"""
Main FastAPI application for Torob AI Assistant
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from router.main_router import MainRouter
from router.base import RouterConfig, RouterState
from agents.general_agent import GeneralAgent
from agents.specific_product import SpecificProductAgent
from agents.features_product import FeaturesProductAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for router and agents
router: Optional[MainRouter] = None
general_agent: Optional[GeneralAgent] = None
specific_product_agent: Optional[SpecificProductAgent] = None
features_product_agent: Optional[FeaturesProductAgent] = None


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


async def initialize_services():
    """Initialize all services and agents"""
    global router, general_agent, specific_product_agent, features_product_agent
    
    try:
        # Load configuration
        config = RouterConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            force_conclusion_turn=int(os.getenv("FORCE_CONCLUSION_TURN", "5"))
        )
        
        # Initialize router
        router = MainRouter(config)
        await router.initialize()
        
        # Initialize individual agents
        general_agent = GeneralAgent(config)
        specific_product_agent = SpecificProductAgent(config)
        features_product_agent = FeaturesProductAgent(config)
        
        logger.info("All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


def get_router() -> MainRouter:
    """Dependency to get router instance"""
    if router is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    return router


def get_general_agent() -> GeneralAgent:
    """Dependency to get general agent instance"""
    if general_agent is None:
        raise HTTPException(status_code=503, detail="General agent not initialized")
    return general_agent


def get_specific_product_agent() -> SpecificProductAgent:
    """Dependency to get specific product agent instance"""
    if specific_product_agent is None:
        raise HTTPException(status_code=503, detail="Specific product agent not initialized")
    return specific_product_agent


def get_features_product_agent() -> FeaturesProductAgent:
    """Dependency to get features product agent instance"""
    if features_product_agent is None:
        raise HTTPException(status_code=503, detail="Features product agent not initialized")
    return features_product_agent


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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Torob AI Assistant API is running",
        version="1.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    router: MainRouter = Depends(get_router)
):
    """
    Main chat endpoint for user interactions
    
    This endpoint processes user messages and returns appropriate responses
    with product recommendations and random keys.
    """
    try:
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Validate chat ID
        if not validate_chat_id(request.chat_id):
            raise HTTPException(status_code=400, detail="Invalid chat ID format")
        
        # Get the latest message (for now, we only process the last message)
        latest_message = request.messages[-1]
        
        # Validate message type
        validate_message_type(latest_message.type)
        
        # For now, only handle text messages
        if latest_message.type == "image":
            # Validate image content
            if not validate_image_content(latest_message.content):
                raise HTTPException(status_code=400, detail="Invalid image content")
            
            return ChatResponse(
                message="متأسفم، در حال حاضر پردازش تصاویر پشتیبانی نمی‌شود. لطفا سوال خود را به صورت متن ارسال کنید.",
                base_random_keys=None,
                member_random_keys=None
            )
        
        # Extract and validate user query
        user_query = validate_text_content(latest_message.content)
        
        # Create router state
        router_state = RouterState(
            user_query=user_query,
            session_context={
                "chat_id": request.chat_id,
                "previous_interactions": []  # Could be enhanced to store conversation history
            },
            turn_count=1  # Could be enhanced to track conversation turns
        )
        
        # Process the query through the router
        result = await router.process_complete(router_state)
        
        # Extract response information
        final_response = result.get("final_response", "متأسفم، خطایی رخ داده است.")
        routing_decision = result.get("routing_decision")
        final_agent = result.get("final_agent", "GENERAL")
        
        # Determine response based on agent type and results
        response_message = final_response
        base_random_keys = None
        member_random_keys = None
        
        # Handle specific product agent response
        if final_agent == "SPECIFIC_PRODUCT":
            specific_response = result.get("specific_product_response", {})
            if specific_response.get("found") and specific_response.get("random_key"):
                base_random_keys = [specific_response["random_key"]]
                response_message = f"محصول مورد نظر شما یافت شد: {specific_response.get('product_name', 'نام محصول')}"
            else:
                response_message = "متأسفم، محصول مورد نظر شما یافت نشد. لطفا اطلاعات بیشتری ارائه دهید."
        
        # Handle features product agent response
        elif final_agent == "PRODUCT_FEATURE":
            features_response = result.get("features_product_response", {})
            if features_response.get("found") and features_response.get("random_key"):
                base_random_keys = [features_response["random_key"]]
                response_message = features_response.get("formatted_features", "ویژگی‌های محصول یافت شد.")
            else:
                response_message = "متأسفم، ویژگی‌های محصول مورد نظر شما یافت نشد."
        
        # Handle general agent response (no specific keys needed)
        elif final_agent == "GENERAL":
            # General agent responses don't need specific product keys
            pass
        
        # Validate and sanitize response
        response_message = sanitize_response_message(response_message)
        base_random_keys = validate_random_keys(base_random_keys, max_count=10)
        member_random_keys = validate_random_keys(member_random_keys, max_count=10)
        
        return ChatResponse(
            message=response_message,
            base_random_keys=base_random_keys,
            member_random_keys=member_random_keys
        )
        
    except HTTPException:
        raise
    except TorobAPIException as e:
        logger.error(f"Torob API error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error processing chat request: {e}")
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
