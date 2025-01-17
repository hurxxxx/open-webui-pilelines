<p align="center">
  <a href="#"><img src="./docs/images/header.png" alt="Pipelines Logo"></a>
</p>

# Pipelines: UI-Agnostic OpenAI API Plugin Framework

> [!TIP]
> If your goal is simply to add support for additional providers like Anthropic or basic filters, you likely don't need Pipelines. For those cases, Open WebUI Functions are a better fit—it's built-in, much more convenient, and easier to configure. Pipelines, however, comes into play when you're dealing with computationally heavy tasks (e.g., running large models or complex logic) that you want to offload from your main Open WebUI instance for better performance and scalability.

Welcome to **Pipelines**, an [Open WebUI](https://github.com/open-webui) initiative. Pipelines bring modular, customizable workflows to any UI client supporting OpenAI API specs – and much more! Easily extend functionalities, integrate unique logic, and create dynamic workflows with just a few lines of code.

## 🚀 Why Choose Pipelines?

- **Limitless Possibilities:** Easily add custom logic and integrate Python libraries, from AI agents to home automation APIs.
- **Seamless Integration:** Compatible with any UI/client supporting OpenAI API specs. (Only pipe-type pipelines are supported; filter types require clients with Pipelines support.)
- **Custom Hooks:** Build and integrate custom pipelines.

### Examples of What You Can Achieve:

- [**Function Calling Pipeline**](/examples/filters/function_calling_filter_pipeline.py): Easily handle function calls and enhance your applications with custom logic.
- [**Custom RAG Pipeline**](/examples/pipelines/rag/llamaindex_pipeline.py): Implement sophisticated Retrieval-Augmented Generation pipelines tailored to your needs.
- [**Message Monitoring Using Langfuse**](/examples/filters/langfuse_filter_pipeline.py): Monitor and analyze message interactions in real-time using Langfuse.
- [**Rate Limit Filter**](/examples/filters/rate_limit_filter_pipeline.py): Control the flow of requests to prevent exceeding rate limits.
- [**Real-Time Translation Filter with LibreTranslate**](/examples/filters/libretranslate_filter_pipeline.py): Seamlessly integrate real-time translations into your LLM interactions.
- [**Toxic Message Filter**](/examples/filters/detoxify_filter_pipeline.py): Implement filters to detect and handle toxic messages effectively.
- [**Auto Knowledge Selection Filter**](https://github.com/hurxxxx/your-repo/blob/main/examples/filters/auto_knowledge_selection_filter.py): Automatically select the most appropriate knowledge base based on user input.
- **And Much More!**: The sky is the limit for what you can accomplish with Pipelines and Python. [Check out our scaffolds](/examples/scaffolds) to get a head start on your projects and see how you can streamline your development process!

## 🔧 How It Works

<p align="center">
  <a href="./docs/images/workflow.png"><img src="./docs/images/workflow.png" alt="Pipelines Workflow"></a>
</p>

Integrating Pipelines with any OpenAI API-compatible UI client is simple. Launch your Pipelines instance and set the OpenAI URL on your client to the Pipelines URL. That's it! You're ready to leverage any Python library for your needs.

## ⚡ Quick Start with Docker

> [!WARNING]
> Pipelines are a plugin system with arbitrary code execution — **don't fetch random pipelines from sources you don't trust**.

For a streamlined setup using Docker:

1. **Run the Pipelines container:**

   ```sh
   docker run -d -p 9099:9099 --add-host=host.docker.internal:host-gateway -v pipelines:/app/pipelines --name pipelines --restart always ghcr.io/open-webui/pipelines:main
   ```

2. **Connect to Open WebUI:**

   - Navigate to the **Settings > Connections > OpenAI API** section in Open WebUI.
   - Set the API URL to `http://localhost:9099` and the API key to `0p3n-w3bu!`. Your pipelines should now be active.

> [!NOTE]
> If your Open WebUI is running in a Docker container, replace `localhost` with `host.docker.internal` in the API URL.

3. **Manage Configurations:**

   - In the admin panel, go to **Admin Settings > Pipelines tab**.
   - Select your desired pipeline and modify the valve values directly from the WebUI.

> [!TIP]
> If you are unable to connect, it is most likely a Docker networking issue. We encourage you to troubleshoot on your own and share your methods and solutions in the discussions forum.

If you need to install a custom pipeline with additional dependencies:

- **Run the following command:**

  ```sh
  docker run -d -p 9099:9099 --add-host=host.docker.internal:host-gateway -e PIPELINES_URLS="https://github.com/hurxxxx/your-repo/blob/main/examples/filters/auto_knowledge_selection_filter.py" -v pipelines:/app/pipelines --name pipelines --restart always ghcr.io/open-webui/pipelines:main
  ```

Alternatively, you can directly install pipelines from the admin settings by copying and pasting the pipeline URL, provided it doesn't have additional dependencies.

That's it! You're now ready to build customizable AI integrations effortlessly with Pipelines. Enjoy!

## 📦 Installation and Setup

Get started with Pipelines in a few easy steps:

1. **Ensure Python 3.11 is installed.**
2. **Clone the Pipelines repository:**

   ```sh
   git clone https://github.com/hurxxxx/your-repo.git
   cd your-repo
   ```

3. **Install the required dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Start the Pipelines server:**

   ```sh
   sh ./start.sh
   ```

Once the server is running, set the OpenAI URL on your client to the Pipelines URL. This unlocks the full capabilities of Pipelines, integrating any Python library and creating custom workflows tailored to your needs.

## 📂 Directory Structure and Examples

The `/pipelines` directory is the core of your setup. Add new modules, customize existing ones, and manage your workflows here. All the pipelines in the `/pipelines` directory will be **automatically loaded** when the server launches.

You can change this directory from `/pipelines` to another location using the `PIPELINES_DIR` environment variable.

### Integration Examples

Find various integration examples in the `/examples` directory. These examples show how to integrate different functionalities, providing a foundation for building your own custom pipelines.

- **Auto Knowledge Selection Filter**: Automatically selects the most appropriate knowledge base based on user input. [View Example](https://github.com/hurxxxx/your-repo/blob/main/examples/filters/auto_knowledge_selection_filter.py)

## 🎉 Work in Progress

We’re continuously evolving! We'd love to hear your feedback and understand which hooks and features would best suit your use case. Feel free to reach out and become a part of our Open WebUI community!

Our vision is to push **Pipelines** to become the ultimate plugin framework for our AI interface, **Open WebUI**. Imagine **Open WebUI** as the WordPress of AI interfaces, with **Pipelines** being its diverse range of plugins. Join us on this exciting journey! 🌍

---

## 📄 Example: Auto Knowledge Selection Filter

Below is an example of the **Auto Knowledge Selection Filter** implemented in our Pipelines framework. This filter automatically selects the most appropriate knowledge base based on the user's input.

### `auto_knowledge_selection_filter.py`

```python
title: Auto Knowledge Selection Filter
author: hurxxxx
author_url: https://github.com/hurxxxx
funding_url: https://github.com/hurxxxx
version: 0.1.0
required_open_webui_version: 0.5.0 +
```

```python
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
```

### Features

- **Automatic Knowledge Base Selection:** Analyzes user input to select the most relevant knowledge base.
- **Real-Time Feedback:** Emits status updates during the selection process.
- **Error Handling:** Gracefully handles errors and provides informative status messages.
- **Extensible:** Easily integrate additional logic or modify existing functionality to suit your needs.

### Usage

1. **Add the Filter to Your Pipelines:**

   Ensure the `auto_knowledge_selection_filter.py` is placed in the `/examples/filters/` directory of your Pipelines setup.

2. **Configure Dependencies:**

   If your filter requires additional Python libraries, update the Docker run command or install them manually as needed.

3. **Activate the Filter:**

   Through the Open WebUI admin panel, navigate to **Admin Settings > Pipelines tab**, select the **Auto Knowledge Selection Filter**, and enable it.

4. **Customize as Needed:**

   Modify the filter logic to better align with your specific requirements or integrate with other systems.

## 🔗 Links

- **GitHub Repository:** [https://github.com/hurxxxx/your-repo](https://github.com/hurxxxx/your-repo)
- **Open WebUI:** [https://github.com/open-webui](https://github.com/open-webui)
- **Pipelines Documentation:** [./docs](./docs)

Feel free to explore, contribute, and extend Pipelines to unlock the full potential of your AI integrations!