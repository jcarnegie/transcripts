from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import ChatMessage, AIMessage
import openai
from typing import AsyncGenerator, Optional, Tuple
from server.chat import Conversation
import logging
from vocode import getenv
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.agent.utils import stream_openai_response_async


class ChatGPTAgent(BaseAgent):
    def __init__(
            self,
            name: str,
            job_title: str,
            speaking_style: str,
            agent_config: ChatGPTAgentConfig,
            logger: logging.Logger = None,
            openai_api_key: Optional[str] = None,
    ):
        super().__init__(agent_config)
        self.name = name
        self.job_title = job_title
        self.speaking_style = speaking_style
        openai.api_key = openai_api_key or getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed in")
        self.agent_config = agent_config
        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(agent_config.prompt_preamble),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )
        self.memory = ConversationBufferMemory(return_messages=True)
        if agent_config.initial_message:
            if (
                    agent_config.generate_responses
            ):  # we use ChatMessages for memory when we generate responses
                self.memory.chat_memory.messages.append(
                    ChatMessage(
                        content=agent_config.initial_message.text, role="assistant"
                    )
                )
            else:
                self.memory.chat_memory.add_ai_message(
                    agent_config.initial_message.text
                )
        self.llm = ChatOpenAI(
            model_name=self.agent_config.model_name,
            temperature=self.agent_config.temperature,
            max_tokens=self.agent_config.max_tokens,
            openai_api_key=openai.api_key,
        )
        # self.conversation = ConversationChain(
        #     memory=self.memory, prompt=self.prompt, llm=self.llm
        # )
        self.conversation = Conversation(
            name=self.name, job_title=self.job_title, speaking_style=self.speaking_style,
        )
        self.first_response = (
            self.create_first_response(agent_config.expected_first_prompt)
            if agent_config.expected_first_prompt
            else None
        )
        self.is_first_response = True

    def create_first_response(self, first_prompt):
        return self.conversation.predict(input=first_prompt)

    async def respond(self, human_input: str, is_interrupt: bool = False, conversation_id: Optional[str] = None) -> Tuple[str, bool]:
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            self.memory.chat_memory.add_user_message(human_input)
            self.memory.chat_memory.add_ai_message(cut_off_response)
            return cut_off_response, False

        self.logger.debug("LLM responding to human input")

        if self.is_first_response and self.first_response:
            self.logger.debug("First response is cached")
            self.is_first_response = False
            text = self.first_response
        else:
            text = await self.conversation.apredict(input=human_input)

        self.logger.debug(f"LLM response: {text}")

        return text, False

    async def generate_response(
            self, human_input: str, is_interrupt: bool = False, conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        self.memory.chat_memory.messages.append(ChatMessage(role="user", content=human_input))

        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            self.memory.chat_memory.messages.append(
                ChatMessage(role="assistant", content=cut_off_response)
            )
            yield cut_off_response
            return

        prompt = self.conversation.get_prompt(human_input)
        bot_memory_message = ChatMessage(role="assistant", content="")
        self.memory.chat_memory.messages.append(bot_memory_message)

        stream = await openai.Completion.acreate(
            model=self.agent_config.model_name,
            prompt=prompt,
            max_tokens=self.agent_config.max_tokens,
            temperature=self.agent_config.temperature,
            stream=True,
        )
        async for message in stream_openai_response_async(
            stream,
            get_text=lambda choice: choice.get("text"),
        ):
            bot_memory_message.content = f"{bot_memory_message.content} {message}"
            yield message
            
    def update_last_bot_message_on_cut_off(self, message: str):
        for memory_message in self.memory.chat_memory.messages[::-1]:
            if (
                isinstance(memory_message, ChatMessage)
                and memory_message.role == "assistant"
            ) or isinstance(memory_message, AIMessage):
                memory_message.content = message
                return
