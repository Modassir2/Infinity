# Infinity

Infinity is a desktop-first AI assistant that runs in the terminal and can switch tool sets dynamically based on the task. It supports local OpenAI-compatible model backends, desktop screen interaction, web research, file-system operations, and document/image reading.

It is designed for:
- local-first AI workflows
- desktop automation and inspection
- file and project management
- research and source-backed answers
- persistent memory and conversation history

## Features

- Local or cloud OpenAI-compatible model support
- Desktop screenshot capture and visual context
- Multi-monitor support via `primary_monitor`
- Tool-set switching at runtime with `get_tools`
- Web search using a configured SearxNG instance
- Wikipedia lookup support
- File and directory management tools
- Reading support for plain text, CSV, JSON, PDF, DOCX, and images
- Persistent chat history and memory consolidation
- Rich terminal UI with markdown formatting

## Requirements

- Python 3.8+
- An OpenAI-compatible LLM endpoint
- Optional: local model server such as Ollama, vLLM, or a compatible server behind a local URL

## Dependencies

Install the project dependencies with:

```bash
pip install -r requirements.txt
```

The project includes these core packages:

- openai
- rich
- requests
- pyautogui
- mss
- opencv-python
- numpy
- pywin32
- pillow
- python-docx
- pypdf
- wikipedia-api
- curl_cffi
- beautifulsoup4

## Quick Start

### 1) Clone the project

```bash
git clone https://github.com/Modassir2/Infinity
cd Infinity
```

### 2) Create a virtual environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install requirements

```bash
pip install -r requirements.txt
```

### 4) Configure the app

Edit `config.json` with your model and server information.

Example:

```json
{
  "base_url": "http://127.0.0.1:8002",
  "context_length": 32768,
  "buffer_token": 4096,
  "api_key": "your-api-key",
  "model_id": "qwen3.5_4b",
  "primary_monitor": 2,
  "screen_resolution": { "x": 1920, "y": 1080 },
  "keep_images": 1,
  "searxng_url": "http://127.0.0.1:8005",
  "n_retry": 3,
  "max_characters": 9000
}
```

### Configuration options

- `base_url`: Base URL of the OpenAI-compatible server, defaults to OpenAI
- `context_length`: Maximum context window for the model, defaults to 8192 tokens
- `buffer_token`: Reserved token buffer before truncation, defaults to 2048 tokens
- `api_key`: API key for authentication
- `model_id`: Model name to use
- `primary_monitor`: monitor number for screenshot tools, defaults to 1
- `screen_resolution`: screen size for the selected write target, defaults to { "x": 1920, "y": 1080 }
- `keep_images`: maximum number of screenshots/images retained in context, defaults to 999
- `searxng_url`: URL of a SearxNG instance for web search, defaults to None i.e `web_search` tool wont work, fall back to `wiki_search` tool
- `n_retry`: retry count for external requests
- `max_characters`: max character length for fetched web content, defaults to 10k characters

Important:
- `api_key` and `model_id` are required
- other fields are optional and fall back to defaults

## Running Infinity

From the project root:

```bash
.venv/Scripts/activate #on Windows
source .venv/bin/activate #on Mac/Linux
python main.py
```

You can also run the app from the included Windows launcher (`Infinity AI.bat`) if available in your environment.

## Command shortcuts

The app supports these commands from the CLI:

- `/help` — show command help
- `/image <path>` — attach an image by full path
- `/remove_imgs` — clear attached images from the current message
- `/clear_imgs` — remove images from the history context
- `/clear` — clear the conversation history
- `/update` — reload configuration and memory settings
- `/tokens` — show token usage
- `/memory` — show active memory profile
- `/general_tools` — switch back to the general tool set
- `/tools` — show the active tool set
- `/del` — delete current conversation context
- `/exit` or `/bye` — exit the app

## Tool sets

Infinity uses dynamic tool sets. The main app can switch between:

- `general_tools`
- `web_search_tools`
- `desktop_tools`
- `file_management_tools`
- `read_file_tools`

### Global tools

Available globally:
- `get_tools`
- `view_screen`
- `update_memory`

### Web search tools

- `get_weather`
- `wiki_search`
- `web_search`
- `fetch_url_content`

### Desktop tools

The desktop toolset supports:
- `screenshot capture`
- `left_click`
- `right_click`
- `typing_text`
- `keyboard_shortcuts`
- `scrolling`
- `waiting`
- `shortcut search`

### File management tools

The file management toolset supports:
- `set_base_dir`
- `make_dir`
- `delete_dir`
- `list_dir`
- `rename_dir`
- `search_dir`
- `create_file`
- `patch_file`
- `write_file`
- `read_file`
- `read_metadata`
- `rename_file`
- `delete_file`

### Read-file tools

The specialized read toolset supports:
- `read_pdf`
- `read_image`
- `read_plain_text`
- `read_csv`
- `find_in_file`
- `read_json`
- `read_docx`

## Project structure

```text
Infinity/
├── main.py
├── classes.py
├── utils.py
├── config.json
├── global_tools.json
├── README.md
├── requirements.txt
├── LICENSE
├── Experimental.ipynb
├── functions/
│   ├── desktop_functions.py
│   ├── file_managment_functions.py
│   ├── read_file_functions.py
│   └── web_search_tools.py
├── tools_schema/
│   ├── desktop_tools.json
│   ├── file_management_tools.json
│   ├── read_file_tools.json
│   ├── web_search_tools.json
│   └── global_tools.json
├── requirements/
│   ├── desktop_requirements.txt
│   ├── file_managment_requirements.txt
│   ├── read_file_requirements.txt
│   ├── web_search_requirements.txt
│   └── minimum_requirements.txt
├── data/
│   ├── history.json
│   ├── memory.md
│   └── Shortcuts.md
└── .venv/          # local virtual environment
```

## Core architecture

### `Config`
Loads and validates application settings. Creates the OpenAI-compatible client and stores runtime config values such as:
- model URL
- API key
- model name
- token settings
- display configuration
- image retention count

### `History`
Tracks conversation context and token use. It:
- stores chat messages
- truncates old history when approaching token limits
- compresses memory based on recent conversation
- keeps the system prompt updated with current date and active tool set

### `ToolSet`
Contains:
- active tool set name
- tool schema list
- tool execution map

### `utils.py`
Contains supporting functions for:
- loading configuration and schemas
- memory persistence
- datetime formatting
- token counting
- logging
- history saving/loading

## Memory system

Infinity stores a markdown memory profile in `data/memory.md`. The app uses a memory consolidation step to summarize older conversation content and preserve important user preferences, facts, and context.

This is especially useful when:
- the user asks to remember something
- the assistant needs to retain ongoing task context
- long-running conversations benefit from compact summaries

## Security and safety

- Local-first configuration is encouraged
- file-management tools validate paths and prevent directory traversal
- the app keeps operations scoped to the active base directory
- screenshots and attached images are kept under configurable limits

## Troubleshooting

### LLM connection issues
- verify the `base_url` is correct
- ensure the model server is running
- confirm `api_key` and `model_id` are valid

### Screenshot or desktop tools not working
- verify `primary_monitor` is set to the correct display
- check `screen_resolution` is accurate for the monitor
- ensure desktop automation dependencies are installed

### Memory or context problems
- reduce `context_length` or increase `buffer_token` if needed
- use `/clear` or `/del` to reset conversation state

### Web search not working
- confirm `searxng_url` is configured correctly
- make sure the SearxNG service is reachable
- check that the backend can accept search requests

## Development notes

The app is structured so new tool groups can be added with a few steps:

1. create a tool module in `functions/`
2. define the tool schemas in `tools_schema/`
3. add the tool map and instructions in `main.py` in `tool_set_map`
4. update dependencies if needed

This keeps the system modular without needing a large rewrite.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Pull requests, improvements, and issue reports are welcome. The project is intended to stay lightweight, modular, and practical for local AI workflows.