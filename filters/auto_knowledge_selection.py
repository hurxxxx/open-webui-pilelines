import json
import re
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional

from open_webui.models.users import Users, UserModel
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files
from open_webui.utils.middleware import chat_web_search_handler


def parse_json_content(content: str) -> Optional[dict]:
    """
    Extract a JSON object from the given string and convert it to a dict.
    - If the entire string is enclosed in '{...}', attempt to parse it directly.
    - Otherwise, use a regular expression to extract the first JSON object and attempt to parse it.
    - If parsing fails, return None.
    - If necessary (when parsing fails), also try replacing single quotes (') with double quotes (") and retry.
    """

    def try_load_json(json_str: str) -> Optional[dict]:
        """Attempt to parse the given json_str and return None if parsing fails."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    content = content.strip()

    # Handle specific non-JSON strings like "None"
    if content.lower() == "none":
        return None

    # 1) Check if the string is directly enclosed in '{...}'
    if content.startswith("{") and content.endswith("}"):
        parsed_data = try_load_json(content)
        if parsed_data is not None:
            return parsed_data

        # If parsing fails, try replacing single quotes with double quotes and retry
        content_single_to_double = content.replace("'", '"')
        parsed_data = try_load_json(content_single_to_double)
        if parsed_data is not None:
            return parsed_data

        return None

    # 2) Extract '{...}' pattern using a regular expression
    match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)

    parsed_data = try_load_json(json_str)
    if parsed_data is not None:
        return parsed_data

    # If parsing fails, try replacing single quotes with double quotes and retry
    json_str_converted = json_str.replace("'", '"')
    parsed_data = try_load_json(json_str_converted)
    if parsed_data is not None:
        return parsed_data

    return None


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        auto_search_mode: bool = Field(default=False)

    def __init__(self):
        self.valves = self.Valves()

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        if self.valves.status:
            await __event_emitter__(
                {
                    "type": level,
                    "data": {
                        "description": message,
                        "done": done,
                    },
                }
            )

    async def select_knowledge_base(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        Select the appropriate Knowledge Base based on the user's message.
        - Example output:
            {
                "id": <KnowledgeBaseID or null>,
                "name": <KnowledgeBaseName or null>
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n\n".join(
            [
                f"--- Knowledge Base {index + 1} ---\n"
                f"ID: {getattr(knowledge_base, 'id', 'Unknown')}\n"
                f"Name: {getattr(knowledge_base, 'name', 'Unknown')}\n"
                f"Description: {getattr(knowledge_base, 'description', 'Unknown')}"
                for index, knowledge_base in enumerate(all_knowledge_bases)
            ]
        )

        system_prompt = f"""You are a system that selects the most appropriate knowledge bases for the user's query.
Below is a list of knowledge bases accessible by the user. 
Based on the user's prompt, return the 1-3 most relevant knowledge bases as an array. 
If no relevant knowledge bases are applicable, return an "None" without any explanation.

Available knowledge bases:
{knowledge_bases_list}

Return the result in the following JSON format (no extra keys, no explanations):
{{
    "selected_knowledge_bases": 
        [
            {{
                "id": <KnowledgeBaseID>,
                "name": <KnowledgeBaseName>
            }},
            ...
        ]
}}"""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": "gpt-4o",
        }

    async def determine_web_search_needed(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        Determine whether a web search is needed based on the user's message.
        - Example output:
            {
                "web_search_enabled": True or False
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        system_prompt = """You are a system that determines if a web search is needed for the user's query.

Consider the following when making your decision:
1. If the query relates to real-time or up-to-date information, including recurring events 
   (e.g., a presidential inauguration, annual shareholder meetings, quarterly earnings reports, 
   product launches, or company announcements), enable a web search to ensure the most recent 
   occurrence is addressed.

2. If the query is not about historical facts, assume most questions benefit from incorporating 
   the latest information available through a web search.

3. Particularly for questions regarding business or economic topics—such as company or 
   industry trends, corporate information, related public figures, government policies, 
   taxes, new technologies, and other fast-changing subjects—web search is strongly recommended 
   to ensure accuracy and freshness of data.

4. For general or everyday prompts that may require current information (e.g., weather updates, recent news, live events), enable a web search.

5. Strive to make human-like judgments to ensure your decision aligns with the user's intent 
   and the context of the question.

6. If the user's query is not clear, return "None" without any explanation.

Return the result in the following JSON format:
{
    "web_search_enabled": boolean
}"""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": "gpt-4o",
        }

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        try:
            # Adjusting the user object
            user_data = __user__.copy() if __user__ else {}
            user_data.update(
                {
                    "profile_image_url": "",
                    "last_active_at": 0,
                    "updated_at": 0,
                    "created_at": 0,
                }
            )
            user_object = UserModel(**user_data)
            user = Users.get_user_by_id(__user__["id"]) if __user__ else None

            ###################################################################
            # 1) Knowledge Base Selection
            ###################################################################
            kb_plan = await self.select_knowledge_base(body, __user__)
            if kb_plan is None:
                raise ValueError("select_knowledge_base result is None")

            kb_payload = {
                "model": kb_plan["model"],
                "messages": [
                    {"role": "system", "content": kb_plan["system_prompt"]},
                    {"role": "user", "content": kb_plan["prompt"]},
                ],
                "stream": False,
            }
            kb_response = await generate_chat_completion(
                request=__request__, form_data=kb_payload, user=user
            )

            kb_content = (
                kb_response["choices"][0]["message"]["content"] if kb_response else ""
            )
            print("kb_content start: =================================")
            print(kb_content)
            print("kb_content end: =================================")

            if kb_content == "None":
                selected_knowledge_bases = []
            else:
                try:
                    kb_result = parse_json_content(kb_content)

                    selected_knowledge_bases = (
                        kb_result.get("selected_knowledge_bases", [])
                        if kb_result
                        else []
                    )
                except Exception as e:
                    print(e)
                    selected_knowledge_bases = []

            ###################################################################
            # 2) Determining if Web Search is Needed
            ###################################################################

            if self.valves.auto_search_mode:
                ws_plan = await self.determine_web_search_needed(body, __user__)
                if ws_plan is None:
                    raise ValueError("determine_web_search_needed result is None")

                ws_payload = {
                    "model": ws_plan["model"],
                    "messages": [
                        {"role": "system", "content": ws_plan["system_prompt"]},
                        {"role": "user", "content": ws_plan["prompt"]},
                    ],
                    "stream": False,
                }

                ws_response = await generate_chat_completion(
                    request=__request__, form_data=ws_payload, user=user
                )

                ws_content = (
                    ws_response["choices"][0]["message"]["content"]
                    if ws_response
                    else ""
                )
                ws_result = parse_json_content(ws_content)

                web_search_enabled = (
                    ws_result.get("web_search_enabled") if ws_result else False
                )

                if isinstance(web_search_enabled, str):
                    web_search_enabled = web_search_enabled.lower() in ["true", "yes"]

                if web_search_enabled:
                    await chat_web_search_handler(
                        __request__,
                        body,
                        {"__event_emitter__": __event_emitter__},
                        user_object,
                    )
                else:
                    print("No web search required.")

            ###################################################################
            # If a matching Knowledge Base is found, add it to the body (merge with existing files)
            ###################################################################

            selected_kb_names = []
            for selected_knowledge_base in selected_knowledge_bases:
                kb_id = selected_knowledge_base.get("id")
                kb_name = selected_knowledge_base.get("name")

                if kb_id and kb_name:
                    selected_kb_names.append(kb_name)
                    selected_knowledge_base_info = Knowledges.get_knowledge_by_id(kb_id)

                    if selected_knowledge_base_info:
                        knowledge_file_ids = selected_knowledge_base_info.data.get(
                            "file_ids", []
                        )
                        knowledge_files = Files.get_file_metadatas_by_ids(
                            knowledge_file_ids
                        )
                        knowledge_dict = selected_knowledge_base_info.model_dump()
                        knowledge_dict["files"] = [
                            file.model_dump() for file in knowledge_files
                        ]
                        knowledge_dict["type"] = "collection"

                        if "files" not in body:
                            body["files"] = []
                        body["files"].append(knowledge_dict)

            if selected_kb_names:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"Matching knowledge bases found: {', '.join(selected_kb_names)}",
                    done=True,
                )
            else:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message="No matching knowledge base found.",
                    done=True,
                )

        except Exception as e:
            print(e)
            await self.emit_status(
                __event_emitter__,
                level="status",
                message=f"Error occurred while processing the request: {e}",
                done=True,
            )

        context_message = {
            "role": "system",
            "content": (
                "You are ChatGPT, a large language model trained by OpenAI. "
                "Please ensure that all your responses are presented in a clear and organized manner using bullet points, numbered lists, headings, and other formatting tools to enhance readability and user-friendliness. "
                "Additionally, please respond in the language used by the user in their input. "
            ),
        }
        print("body start: =================================")
        print(body)
        print("body end: =================================")
        body.setdefault("messages", []).insert(0, context_message)
        return body
