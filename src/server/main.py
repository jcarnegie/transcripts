import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.client_backend.conversation import ConversationRouter
from vocode.streaming.models.client_backend import OutputAudioConfig
from .chat_agent import ChatGPTAgent
from .logger import logger


jessica_voice_id = 'eXrR6xbayO5ns8SFE3zc'
app = FastAPI(docs_url=None)
templates = Jinja2Templates(directory="templates")
REPLIT_URL = f"{os.getenv('REPL_SLUG')}.{os.getenv('REPL_OWNER')}.repl.co"


@app.get("/")
async def root(request: Request):
    env_vars = {
        "REPLIT_URL": REPLIT_URL,
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "DEEPGRAM_API_KEY": os.environ.get("DEEPGRAM_API_KEY"),
        "ELEVEN_LABS_API_KEY": os.environ.get("ELEVEN_LABS_API_KEY"),
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "env_vars": env_vars
    })


def main():
    jessica_speaking_style = '''
        Jessica has a very calm and relaxed speaking style. She speaks in a slow and considered manner, 
        emphasizing certain words for emphasis. She shows strong empathy and understanding throughout 
        her speaking, helping her audience to relate to her and fully understand her point. She uses 
        thoughtful language and encourages her audience to reflect on their own experiences, making her 
        speaking very engaging and effective. Jessica has a very articulate speaking style, with 
        well-structured sentences that convey her points clearly. She speaks in a comforting and 
        friendly tone, using language that is engaging and easy to understand. Her words have a 
        calming and soothing effect, making her audience more likely to listen and take in her message. 
        She is open and honest about her thoughts and feelings while speaking, further connecting her 
        to her audience, and she shows genuine interest in their own experiences.'''

    agent_config = ChatGPTAgentConfig(
        prompt_preamble="Greet me with enthusiasm",
        model_name="text-davinci-003"
    )

    agent = ChatGPTAgent(
        name='Jessica',
        job_title='Relationship Coach',
        speaking_style=jessica_speaking_style,
        agent_config=agent_config
    )

    def get_synthesizer(output_audio_config: OutputAudioConfig) -> ElevenLabsSynthesizer:
        synthesizer = ElevenLabsSynthesizer(
            ElevenLabsSynthesizerConfig.from_output_audio_config(
                output_audio_config,
                stability=0.2,
                similarity_boost=0.8,
                voice_id=jessica_voice_id,
                api_key=os.getenv("ELEVEN_LABS_API_KEY"),
            ))

        return synthesizer

    conversation_router = ConversationRouter(
        agent=agent,
        synthesizer_thunk=get_synthesizer,
        logger=logger,
    )

    app.include_router(conversation_router.get_router())

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
