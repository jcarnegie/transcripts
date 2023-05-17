import openai
openai.api_key = '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'
import re
from typing import Generator, Optional, Tuple
from vocode.streaming.models.agent import AgentConfig
MAX_TOKENS = 4000

def extract_sentences_with_word(text, word):
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Extract sentences containing the word
    result = [sentence for sentence in sentences if re.search(r'\b{}\b'.format(word), sentence)]

    return result

class Conversation():
    def __init__(self, name, job_title, writing_style):
        self.name = name
        self.job_title = job_title
        self.writing_style = writing_style
        self.messages = []
        self.statements_about_me = []

    def about_me(self):
        return self.name + " is a " + self.job_title \
            + "\n\nHere is a description of their writing style:\n" + self.writing_style \
            + f"\n\nHere are some things {self.name} has said about themselves: " \
            + "\n".join(self.statements_about_me)

    def get_clone_prompt(self):
        return "Here is a conversation between Jessica and her clone: \n\n" \
               "Human: You are a clone of me.  " \
               "I am going to teach you to be like me, and you are going to respond to me as if you are me.  " \
               "You are also going to tell me what you think about life and how you handle different situations. " \
               "\n\n"

    def get_relevant_statements(self, input, max_tokens):
        return ""
        # return f"\n\nHere are some things {self.name} has said:\n\n"

    def get_next_message(self, input):
        sentences = extract_sentences_with_word(input, "I")
        self.statements_about_me += sentences

        first_part_of_prompt = self.about_me()

        last_part_of_prompt = self.get_clone_prompt() \
            + "\n\n".join(self.messages[-10:] if len(self.messages) > 10 else self.messages) \
            + "\n\nHuman: " + input \
            + "\n\nAI:"

        total_tokens_used = len(first_part_of_prompt.split(' ')) + len(last_part_of_prompt.split(' '))
        relevant_statements = self.get_relevant_statements(input, max_tokens=MAX_TOKENS-total_tokens_used)

        prompt = first_part_of_prompt + relevant_statements + last_part_of_prompt

        # create a chat completion
        completion = openai.Completion.create(model="text-davinci-003",
                                              prompt=prompt,
                                              temperature=0.9,
                                              max_tokens=150,
                                              presence_penalty=0.5,
                                              frequency_penalty=0.5,
                                              stop=["Human:","AI:"])

        # add the response to the conversation
        ai_message = completion.choices[0].text
        self.messages.append(ai_message)
        return ai_message

    def get_initial_message(self):
        return self.get_next_message("Please greet me with excitement.")

class ConversationAgentConfig(AgentConfig):
    name: str = None
    job_title: str = None
    writing_style: str = None

    def __init__(self, name, job_title, writing_style):
        self.name = name
        self.job_title = job_title
        self.writing_style = writing_style



from vocode.streaming.agent.base_agent import BaseAgent
class ConversationAgent(BaseAgent):
    def __init__(self, name, job_title, writing_style):
        self.agent_config = AgentConfig()
        self.conversation = Conversation(name, job_title, writing_style)

    def respond(
        self,
        human_input,
        is_interrupt: bool = False,
        conversation_id: Optional[str] = None,
    ) -> Tuple[str, bool]:
        response = self.conversation.get_next_message(human_input)
        return response, False

    def generate_response(
        self,
        human_input,
        is_interrupt: bool = False,
        conversation_id: Optional[str] = None,
    ) -> Generator[str, None, None]:
        response = self.conversation.get_next_message(human_input, is_interrupt=is_interrupt, conversation_id=conversation_id)
        yield response


jessica_writing_style = 'Jessica has a very calm and relaxed speaking style. She speaks in a slow and considered manner, emphasizing certain words for emphasis. She shows strong empathy and understanding throughout her speaking, helping her audience to relate to her and fully understand her point. She uses thoughtful language and encourages her audience to reflect on their own experiences, making her speaking very engaging and effective. Jessica has a very articulate speaking style, with well-structured sentences that convey her points clearly. She speaks in a comforting and friendly tone, using language that is engaging and easy to understand. Her words have a calming and soothing effect, making her audience more likely to listen and take in her message. She is open and honest about her thoughts and feelings while speaking, further connecting her to her audience, and she shows genuine interest in their own experiences.'

