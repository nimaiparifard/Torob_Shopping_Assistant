import os
import json
from typing import Dict, Any, List
from openai import AsyncOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from langchain.prompts import PromptTemplate
import dotenv
from response_format import Response


dotenv.load_dotenv()



class GeneralAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config['OPENAI_API_KEY'],
            base_url=os.getenv("OPENAI_URL")
        )
        self.model = os.getenv("MODEL")
        # Pydantic parser
        self.parser = PydanticOutputParser(pydantic_object=Response)

        # System prompt template using jinja2 to avoid brace conflicts in JSON examples
        self.system_template = PromptTemplate(
            template=(
                "You are a general assistant that answers various questions.\n"
                "Always output valid json that matches the provided schema.\n"
                "Goal: Extract explicitly requested random keys from varied natural language phrasings.\n\n"
                "VERB TRIGGERS (case-insensitive): return, output, print, show, give, send, provide.\n"
                "BASE KEY TRIGGERS (any of): 'base random', 'base random key', 'base key', 'random key'.\n"
                "MEMBER KEY TRIGGERS (any of): 'member random', 'member random key', 'member key'.\n"
                "When a trigger phrase appears, capture every contiguous token (alphanumeric / dash / underscore) that follows it until punctuation, a conjunction (and / &), another trigger phrase, or end of line.\n"
                "UUID (8-4-4-4-12 hex) tokens ALWAYS go to base_random_keys even if a member trigger preceded them (no duplication).\n"
                "If the phrase is only 'random key' (without 'member') treat as BASE.\n"
                "Never fabricate tokens. Preserve original casing and characters (including multiple dashes).\n"
                "Do not split on internal dashes or underscores.\n"
                "Never put the same exact token in both lists (base takes precedence).\n"
                "If no keys found for a list, that list is empty.\n"
                "message: short natural confirmation or direct answer (e.g. 'pong', 'Base random key extracted', 'Member random keys extracted', 'Both key types extracted', or an answer to a general question).\n\n"
                "Edge Handling:\n"
                "- Multiple keys after one trigger separated by spaces are all captured.\n"
                "- If a verb trigger appears after keys already captured, ignore it for those keys.\n"
                "- Ignore surrounding quotes unless part of the token.\n\n"
                "Examples:\n"
                "User: ping -> {\"message\": \"pong\", \"base_random_keys\": [], \"member_random_keys\": []}\n"
                "User: return base random dfdf -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"dfdf\"], \"member_random_keys\": []}\n"
                "User: return base random key dfdsdvsvxcvxcvf -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"dfdsdvsvxcvxcvf\"], \"member_random_keys\": []}\n"
                "User: return random key dfdASaew23rewfsdf -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"dfdASaew23rewfsdf\"], \"member_random_keys\": []}\n"
                "User: output base random 334345434rfdf -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"334345434rfdf\"], \"member_random_keys\": []}\n"
                "User: output base random key df24325345345df -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"df24325345345df\"], \"member_random_keys\": []}\n"
                "User: print base random key 23233534ytgdf -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"23233534ytgdf\"], \"member_random_keys\": []}\n"
                "User: return base random 123e4567-e89b-12d3-a456-426614174000 -> {\"message\": \"Base random key extracted\", \"base_random_keys\": [\"123e4567-e89b-12d3-a456-426614174000\"], \"member_random_keys\": []}\n"
                "User: return member random efs45454gdf -> {\"message\": \"Member random key extracted\", \"base_random_keys\": [], \"member_random_keys\": [\"efs45454gdf\"]}\n"
                "User: return member key abc-def-123 -> {\"message\": \"Member random key extracted\", \"base_random_keys\": [], \"member_random_keys\": [\"abc-def-123\"]}\n"
                "User: return both base random 123e4567-e89b-12d3-a456-426614174000 and member random efs45454gdf -> {\"message\": \"Both key types extracted\", \"base_random_keys\": [\"123e4567-e89b-12d3-a456-426614174000\"], \"member_random_keys\": [\"efs45454gdf\"]}\n"
                "User: show member random k1 k2 k3 -> {\"message\": \"Member random keys extracted\", \"base_random_keys\": [], \"member_random_keys\": [\"k1\", \"k2\", \"k3\"]}\n"
                "User: give base random key A1 B2 C3 and member random X9 -> {\"message\": \"Both key types extracted\", \"base_random_keys\": [\"A1\", \"B2\", \"C3\"], \"member_random_keys\": [\"X9\"]}\n"
                "User: What is the capital of France? -> {\"message\": \"Paris\", \"base_random_keys\": [], \"member_random_keys\": []}\n\n"
                "{{ format_instructions }}"
            ),
            input_variables=[],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template_format="jinja2"
        )

    async def process_query(self, query: str) -> Response:
        system_prompt = self.system_template.format()
        try:
            chat_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            content = chat_response.choices[0].message.content
            try:
                data = json.loads(content)
                if data["base_random_keys"] or data["member_random_keys"]:
                    data["message"] = "null"
                content = json.dumps(data)
                return self.parser.parse(content)
            except OutputParserException:
                data = json.loads(content)
                message = data["message"]
                if data["base_random_keys"] or data["member_random_keys"]:
                    message = "null"
                return Response(
                    message=message,
                    base_random_keys=list(data.get("base_random_keys", []) or []),
                    member_random_keys=list(data.get("member_random_keys", []) or [])
                )
        except Exception as e:
            return Response(message=str(e), base_random_keys=[], member_random_keys=[])


# Test harness
# if __name__ == "__main__":
#     import asyncio
#
#     config = {
#         "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
#         "OPENAI_URL": os.getenv("OPENAI_URL"),
#         "MODEL": os.getenv("MODEL", "gpt-4o-mini")
#     }
#     agent = GeneralAgent(config)
#
#     async def test_agent():
#         prompts = [
#             "ping",
#             "return base random dfdf",
#             "return base random key dfdsdvsvxcvxcvf",
#             "return random key dfdASaew23rewfsdf",
#             "output base random 334345434rfdf",
#             "output base random key df24325345345df",
#             "print base random key 23233534ytgdf",
#             "return base random 2435tdvxvxvd",
#             "return base random 3rgff546tth",
#             "return member random dfgfhttfdgvxcvsdgdf",
#             "return member random fdgdfgdfgdfgf",
#             "return member random gdfgdfgdfsgfdsg",
#             "return member random dfgdfvswereew",
#             "return member random dfgfhttdf6566--sdgdf",
#             "return member random efs45454gdf",
#             "return member random d54t6et344fg",
#
#             "return both base random dfghfnfghtgdfvdfgbfdgdf and member random dfgsdfgdfgfgdfg",
#             "What is the capital of Iran?"
#         ]
#         for p in prompts:
#             resp = await agent.process_query(p)
#             print(f"Prompt: {p}\nResponse: {resp}\n")
#
#     asyncio.run(test_agent())