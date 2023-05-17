import openai
import re
from os import getenv
from vocode.streaming.models.agent import AgentConfig
from typing import Any
from .database import vectordb


MAX_TOKENS = 4000
openai.api_key = getenv("OPENAI_API_KEY")


def extract_sentences_with_word(text, word) -> list[str]:
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Extract sentences containing the word
    result = [sentence for sentence in sentences if re.search(r'\b{}\b'.format(word), sentence)]

    return result


class Conversation:
    def __init__(self, name, job_title, speaking_style, mode):
        self.name = name
        self.job_title = job_title
        self.speaking_style = speaking_style
        self.mode = mode
        self.messages = []
        self.statements_about_me = []
        self.vectordb = vectordb(number_of_retrieval_results=3)

    def about_me(self):
        return self.name + " is a " + self.job_title \
            + "\n\nHere is a description of their writing style:\n" + self.speaking_style \
            + f"\n\nHere are some things {self.name} has said about themselves: " \
            + "\n".join(self.statements_about_me)

    @staticmethod
    def get_clone_prompt():
        return "Here is a conversation between Jessica and her clone: \n\n" \
               "Human: You are a clone of me.  " \
               "I am going to teach you to be like me, and you are going to respond to me as if you are me.  " \
               "You are also going to tell me what you think about life and how you handle different situations. " \
               "\n\n"

    @staticmethod
    def get_coaching_prompt():
        return "Here is a conversation between Jessica (coach) and her client: \n\n" \
               "AI: Hello, I am available for you 24/7 to ask me questions and get advice.  " \
               "\n\n"

    def get_relevant_statements(self, input: str, max_tokens: int) -> str:
        relevant_statements = self.vectordb.query(query=input)
        relevant_tokens = " ".join(relevant_statements.split()[:max_tokens])
        relevant_tokens += "." if not relevant_tokens.endswith(".") else ""
        output = f"\n\nHere are some things {self.name} has said:\n{relevant_tokens}\n"
        return output

    def update_statements_about_me(self, input):
        sentences = extract_sentences_with_word(input, "I")
        if sentences:
            self.statements_about_me += sentences
            # remove the last message from the AI
            if self.messages:
                self.messages.pop()

    def get_prompt(self, input):

        first_part_of_prompt = self.about_me()
        if self.mode == 'Coaching':
            last_part_of_prompt = self.get_coaching_prompt()
        else:
            self.update_statements_about_me(input)
            last_part_of_prompt = self.get_clone_prompt()

        last_part_of_prompt += "\n\n".join(self.messages[-10:] if len(self.messages) > 10 else self.messages)
        last_part_of_prompt += "\n\nHuman: " + input + ".  Respond concisely in under 4 sentences, like you are on a phone call.\n\nAI:"

        total_tokens_used = len(first_part_of_prompt.split(' ')) + len(last_part_of_prompt.split(' '))
        relevant_statements = self.get_relevant_statements(input, max_tokens=MAX_TOKENS-total_tokens_used)

        return first_part_of_prompt + relevant_statements + last_part_of_prompt

    def predict(self, input):
        prompt = self.get_prompt(input)
        print("using prompt: " + prompt)

        # create a chat completion
        completion = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.9,
            max_tokens=150,
            presence_penalty=0.5,
            frequency_penalty=0.5,
            stop=["Human:", "AI:"]
        )

        # add the response to the conversation
        ai_message = completion.choices[0].text
        self.messages.append("Human: " + input)
        self.messages.append("AI: " + ai_message)
        return ai_message

    async def apredict(self, **kwargs: Any) -> str:
        """Format prompt with kwargs and pass to LLM.

        Args:
            **kwargs: Keys to pass to prompt template.

        Returns:
            Completion from LLM.

        Example:
            .. code-block:: python

                completion = llm.predict(adjective="funny")
        """
        return (await self.acall(kwargs))[self.output_key]

    def get_initial_message(self):
        return self.predict("Please greet me with excitement.")


class ConversationAgentConfig(AgentConfig):
    name: str = None
    job_title: str = None
    writing_style: str = None

    def __init__(self, name, job_title, writing_style, **data):
        super().__init__(**data)
        self.name = name
        self.job_title = job_title
        self.writing_style = writing_style


jessica_speaking_style = '''
    Jessica has a very calm and relaxed speaking style. She speaks in a slow and considered manner, 
    emphasizing certain words for emphasis. She shows strong empathy and understanding throughout 
    her speaking, helping her audience to relate to her and fully understand her point. She uses thoughtful 
    language and encourages her audience to reflect on their own experiences, making her speaking very 
    engaging and effective. Jessica has a very articulate speaking style, with well-structured sentences 
    that convey her points clearly. She speaks in a comforting and friendly tone, using language that is 
    engaging and easy to understand. Her words have a calming and soothing effect, making her audience 
    more likely to listen and take in her message. She is open and honest about her thoughts and feelings 
    while speaking, further connecting her to her audience, and she shows genuine interest in their 
    own experiences.
'''

if __name__ == "__main__":

    conversation = Conversation(
        name='Jessica',
        job_title='Relationship Coach',
        speaking_style=jessica_speaking_style,
        mode='Coaching'
    )

    while True:
        human_input = input("Client: ")
        while human_input == '':
            human_input = input("Client: ")
        response = conversation.predict(human_input)
        print(f"{response}")
