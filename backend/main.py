# step 1: import all the necessary libraries
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import os
import logging
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError
import re

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

# Initialize global variable for video transcript context
video_transcript_context = ""
def get_video_id(url: str) -> str | None:

    if not url:
        return None
    

    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_transcript(video_id: str) -> tuple[str | None, str | None]:
    """
    Get transcript for a YouTube video
    Returns: (transcript_text, error_message)
    
    Note: youtube-transcript-api v1.0.0+ changed the API:
    - Old: YouTubeTranscriptApi.get_transcript() (static method)
    - New: YouTubeTranscriptApi().fetch() (instance method)
    """
    try:
        logger.info(f"Fetching transcript for video ID: {video_id}")
        
        # Create instance of YouTubeTranscriptApi (required in v1.0.0+)
        youtube_api = YouTubeTranscriptApi()
        
        # Use fetch() method instead of get_transcript()
        transcript_data = youtube_api.fetch(video_id)
        
        # Extract text from transcript data
        # Note: In v1.0.0+, items are FetchedTranscriptSnippet objects with .text attribute
        # NOT dictionaries, so use item.text instead of item['text']
        transcript_text = " ".join([item.text for item in transcript_data])
        logger.info(f"Successfully fetched transcript: {len(transcript_text)} characters")
        return transcript_text, None
        
    except ParseError as e:
        error_msg = (
            "❌ YouTube API Error (XML Parse Error)\n\n"
            "This usually means:\n"
            "• Video doesn't exist or was deleted\n"
            "• Video is private or age-restricted\n"
            "• Invalid video ID\n"
            "• YouTube is blocking the request\n\n"
            "✅ Solutions:\n"
            "1. Verify the video link is correct\n"
            "2. Make sure the video is public\n"
            "3. Try a different video"
        )
        logger.error(f"ParseError for video {video_id}: {str(e)}")
        return None, error_msg
        
    except TranscriptsDisabled as e:
        error_msg = (
            "❌ Transcripts Disabled\n\n"
            "The owner of this video has disabled subtitles.\n"
            "Please try another video with available subtitles."
        )
        logger.error(f"Transcripts disabled for video {video_id}")
        return None, error_msg
        
    except NoTranscriptFound as e:
        error_msg = (
            "❌ No Transcript Found\n\n"
            "This video doesn't have subtitles or captions.\n"
            "Please try a video with:\n"
            "• Manual subtitles (CC)\n"
            "• Auto-generated captions"
        )
        logger.error(f"No transcript found for video {video_id}")
        return None, error_msg
        
    except AttributeError as e:
        # Handle case where fetch method doesn't exist
        error_msg = (
            "⚠️ Library Version Mismatch\n\n"
            f"Error: {str(e)}\n\n"
            "Please reinstall youtube-transcript-api:\n"
            "pip uninstall youtube-transcript-api\n"
            "pip install youtube-transcript-api"
        )
        logger.error(f"AttributeError for video {video_id}: {str(e)}")
        return None, error_msg
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"❌ Unexpected Error: {error_type}\n\n{str(e)}"
        logger.error(f"Unexpected error for video {video_id}: {error_type} - {str(e)}")
        return None, error_msg

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

class YouTubeRequest(BaseModel):
    url: str

@app.post("/process-youtube-video", response_model=ChatResponse, tags=['youtube'])
async def process_youtube_video(request: YouTubeRequest):
    global video_transcript_context
    logger.info(f"Received YouTube URL processing request: {request.url}")

    video_id = get_video_id(request.url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid YouTube URL"
        )

    # Get transcript with detailed error handling
    transcript, error_msg = get_transcript(video_id)
    if not transcript:
        video_transcript_context = ""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=error_msg or "Failed to get transcript. Please try another video."
        )

    video_transcript_context = transcript
    logger.info(f"Video transcript stored in context ({len(transcript)} characters)")

    # Generate AI summary
    prompt = f"Analyze the following video transcript and provide a concise 3-4 sentence summary:\n\n---\n{transcript[:4000]}\n\n---\nSummary:"

    try:
        summary = ai_provider.generate_response(prompt)
        return ChatResponse(
            response=f"✅ Video Summary:\n\n{summary}\n\n💬 You can now ask me questions about this video!",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error generating video summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video summary: {str(e)}"
        )

# step 7: define the chat endpoint
@app.post("/chat", response_model=ChatResponse, tags = ['chat'])

async def chat(request: ChatRequest):
    global video_transcript_context
    try:
        logger.info(f'Received chat request: {request.message[:50]}...')
        user_message = request.message
        if video_transcript_context:
            prompt = f"Please answer the following question based on the video transcript:\n\n---\n{video_transcript_context}\n\n---\n\nQuestion: {user_message}\n\nAnswer:"
            logger.info("Using video transcript context for answer")
        else:
            prompt = user_message
        ai_response = ai_provider.generate_response(prompt)
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

