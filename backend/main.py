# step 1: import all the necessary libraries
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import os
import logging
from dotenv import load_dotenv

# step 2: load the environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title = 'Deepvista quiz API', 
    description = 'API for the Deepvista quiz application', 
    version = '1.0.0')

AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai').lower()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MAX_MESSAGE_LENGTH = 1000

if not OPENAI_API_KEY:
    logger.warning('OPENAI_API_KEY is not set')
else:
    logger.info('OPENAI_API_KEY loaded')

# step 3: add the CORS middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# step 4: define the data models
class HealthResponse(BaseModel):

    status: str
    timestamp: str
    ai_provider: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-17T10:30:00.000Z",
                "ai_provider": "openai"
            }
        }
class ChatRequest(BaseModel):

    message: str = Field(..., min_length = 1, max_length = MAX_MESSAGE_LENGTH)

    @field_validator('message')
    @classmethod
    def validate_message(cls, content: str) -> str:
        content = content.strip()
        if not content:
            raise ValueError("Message cannot be empty")
        return content

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?"
            }
        }

class ChatResponse(BaseModel):

    response: str
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'm doing well, thank you! How can I help you today?",
                "timestamp": "2025-10-17T10:30:00.000Z"
            }
        }

# step 5: define the AI providers

class OPENAIProvider:

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            logger.error('OPENAI_API_KEY is not set')
            self.enabled = False
        else:
            try:
                import openai
                self.client = openai.OpenAI(api_key = self.api_key)
                self.enabled = True
                logger.info('OPENAIProvider initialized')
            except ImportError:
                logger.error('openai package is not installed')
                self.enabled = False
    
    def generate_response(self, user_msg):
        if not self.enabled:
            raise HTTPException(
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail = 'AI provider not available')
        try:
            logger.info(f'Generating response for user message: {user_msg[:50]}...')
            response = self.client.chat.completions.create(
                model = 'gpt-3.5-turbo',
                messages = [
                    {
                        "role": "system", 
                    "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user", 
                        "content": user_msg
                    }
                ],
                max_tokens = 1000,
                temperature = 0.7,
            )
            ai_response = response.choices[0].message.content.strip()
            logger.info(f'Response generated successfully: {ai_response[:50]}...')
            return ai_response
        except Exception as e:
            logger.error(f'Error generating response: {e}')
            raise HTTPException(
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail = f'Error generating response: {str(e)}'
            )

ai_provider = OPENAIProvider()

# step 6: define the health check endpoint
@app.get("/health", response_model=HealthResponse, tags=['health'])
async def health_check():

    logger.info('Health check endpoint called')
    

    if ai_provider.enabled:
        health_status = "healthy"
    else:
        health_status = "unhealthy"
    
    return HealthResponse(
        status=health_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ai_provider=AI_PROVIDER
    )

# step 7: define the chat endpoint
@app.post("/chat", response_model=ChatResponse, tags = ['chat'])

async def chat(request: ChatRequest):
    try:
        logger.info(f'Received chat request: {request.message[:50]}...')
        ai_response = ai_provider.generate_response(request.message)
        response = ChatResponse(
            response = ai_response,
            timestamp = datetime.now(timezone.utc).isoformat()
        )
        logger.info(f'Response generated successfully: {ai_response[:50]}...')
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in chat endpoint: {e}')
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail = f'Internal server error: {str(e)}'
        )


if __name__ == '__main__':
    import uvicorn
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))

    logger.info(f'Starting server on {host}:{port}')
    uvicorn.run(
        "main:app",
        host = host,
        port = port,
        reload = True,
        log_level = 'info'
    )

