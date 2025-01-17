"""
title: Auto Knowledge Selection Filter
author: hurxxxx
author_url: https://github.com/hurxxxx
funding_url: https://github.com/hurxxxx
version: 0.1.0
required_open_webui_version: 0.5.0 +
"""

from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional, Literal
import json
import re

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion  
from open_webui.utils.misc import get_last_user_message

from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files

class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        pass

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any, 
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        messages = body["messages"]
        user_message = get_last_user_message(messages)
                     
        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")

        if self.valves.status:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Searching for appropriate tools...",
                        "done": False,
                    },
                }
            )

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')}\n - Knowledge Base Name: {getattr(knowledge_base, 'name', 'Unknown')}\n - Description: {getattr(knowledge_base, 'description', 'Unknown')}\n"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = f"""Based on the user's prompt, please find the knowledge base that the user desires.
Available knowledge bases:
{knowledge_bases_list}
Please select the most suitable knowledge base from the above list that best fits the user's requirements.
Ensure that your response is in JSON format with only the "id" : KnowledgeID and "name" : Knowledge Name fields. Do not provide any additional explanations.
If there is no suitable or relevant knowledge base, do not select any. In such cases, return None."""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nQuery: {user_message}"
        )
        payload = {
            "model": body["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        selected_knowledge_base = None  # Initialize to None

        try:
            user = Users.get_user_by_id(__user__["id"])

            response = await generate_chat_completion(
                request=__request__, form_data=payload, user=user
            )

            content = response["choices"][0]["message"]["content"]

            if content is not None:
                
                # 1. Remove code blocks
                content = content.replace("```json", "").replace("```", "").strip()
                # 2. Replace single quotes with double quotes
                content = content.replace("'", '"')

                # 3. Attempt to extract JSON object
                pattern = r"\{.*?\}"  # Modified regex to detect JSON object
                match = re.search(pattern, content, flags=re.DOTALL)
                if match:
                    content = match.group(0)
                else:
                    content = None  # If no match found, set content to None

                if content is not None:
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError: {e}")
                        result = None

                    selected_knowledge_base = result.get("id") if isinstance(result, dict) else None

            # If content is None or JSON parsing failed, selected_knowledge_base remains None

            selected_knowledge_base_info = Knowledges.get_knowledge_by_id(selected_knowledge_base) if selected_knowledge_base else None

            # Access dictionary keys
            if selected_knowledge_base_info:
                knowledge_file_ids = selected_knowledge_base_info.data['file_ids']

                # Retrieve file metadata
                knowledge_files = Files.get_file_metadatas_by_ids(knowledge_file_ids)

                # Convert KnowledgeModel object to dict for JSON serialization
                knowledge_dict = selected_knowledge_base_info.model_dump()
                # Add 'files' attribute: Convert FileMetadataResponse objects to dict
                knowledge_dict['files'] = [file.model_dump() for file in knowledge_files]
                knowledge_dict['type'] = 'collection'

                body["files"] = body.get("files", []) + [knowledge_dict]

                if self.valves.status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Matching knowledge base found: {selected_knowledge_base_info.name}",
                                "done": True,
                            },
                        }
                    )
            else:
                if self.valves.status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "No matching knowledge base found.",
                                "done": True,
                            },
                        }
                    )
        except Exception as e:
            print(e)
            if self.valves.status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error occurred while processing the request: {e}",
                            "done": True,
                        },
                    }
                )
            pass

        context_message = {
            "role": "system", 
            "content": (
                "You are ChatGPT, a large language model trained by OpenAI. "
                "Please ensure that all your responses are presented in a clear and organized manner using bullet points, numbered lists, headings, and other formatting tools to enhance readability and user-friendliness. "
                "Additionally, please respond in the language used by the user in their input."
            )
        }
        body.setdefault("messages", []).insert(0, context_message)

             
        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")

        
        return body
