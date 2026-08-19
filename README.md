# Infinity - Desktop Copilot AI Assistant

A powerful multi-agent application that can switch agents as required per task and supports fully local execution for sensitive data. Supports easy addition of custom tools/agents.

## 🌟 Features

- **Runs Fully Locally**: Runs local language models via OpenAI-compatible API and add url + port in config.json
- **Screen Capture**: Desktop screenshot analysis capabilities for context-aware assistance
- **Multi-Monitor Setup Support**: Configurable monitor selection for screenshot capture
- **Wikipedia Integration**: Built-in Wikipedia search functionality
- **Chat History**: Persistent conversation history with message tracking
- **Memory Management**: Advanced memory consolidation system to maintain user context and preferences
- **Tool Mapping**: Extensible tool system for custom functionality
- **Rich Terminal Output**: Color-coded CLI output with formatted text and markdown support

## 📋 Requirements

- Python 3.8+
- Local LLM server (configured via `config.json`) or Cloud API endpoint that is OpenAI-compatible API endpoint

### Dependencies

See [requirements/](requirements/) folder for requirements of each agent.
See [requirements.txt](requirements.txt) for all required dependencies:
- requests==2.34.2
- rich==15.0.0
- mss==10.2.0
- Wikipedia-API==0.15.0
- openai==2.43.0
- pyautogui==0.9.54
- pywin32==311
- opencv-python==4.13.0.92
- numpy==2.4.4

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Modassir2/Infinity
cd Infinity
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

Edit `config.json` to configure your setup:

```json
{
    "base_url": "http://127.0.0.1",
    "port": 8002,
    "context_length": 16384,
    "buffer_token": 4096,
    "api_key": "your-api-key",
    "model_id": "qwen3.5_4b",
    "primary_monitor": 2,
    "screen_resolution": {"x": 1920, "y": 1080},
    "image_tokens": 1032,
    "keep_images": 1
}
```

**Configuration Options:**
- `base_url`: URL of your LLM server, can be local or cloud
  - Default value: OpenAI server url (https://api.openai.com/v1)
- `port`: Port number for the LLM server. Set as Null for cloud
  - Default value: None
- `context_length`: Maximum context window for the model
 - Default value: 8192
- `buffer_token`: Token buffer for response generation
 - Default value: 2048
- `api_key`: API key for authentication
- `model_id`: Model identifier to use
- `primary_monitor`: Monitor number that the model will see for screenshots, for multi-monitor setup
 - Default value: 1 
- `screen_resolution`: Desktop resolution of selected monitor
 - Default value: {'x':1920,'y':1080}
- `image_tokens`: Token estimate for image encoding
 - Default value: 1032
- `keep_images`: Number of images to keep in history, large values slow processing time
 - Default value: 999

**NOTE:**

All values can be omitted from the `config.json` file but the following are required:
- `api_key`
- `model_id`

### Running Infinity

Double click the `run.bat` file to run directly after installation setup is complete! It activates the python venv and runs the main.py

OR

```bash
# Activate venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
# Run Infinity
python main.py
```

This launches the CLI interface where you can interact with the AI assistant directly in your terminal.

Type `/help` to get list of available commands.

## 📁 Project Structure

```
Infinity/
├── main.py                 # CLI entry point and core functionality
├── classes.py              # Core classes (Config, Agent, History)
├── utils.py                # Utility functions
├── config.json             # Configuration file
├── Experimental.ipynb      # Jupyter notebook for experimentation
├── functions/
│   └── desktop_copilot.py  # Desktop copilot tool implementation
├── requirements/
│   ├── required.txt        # Main dependencies
│   └── desktop_copilot.txt # Desktop copilot specific dependencies
├── tools_schema/
│   ├── desktop_copilot.json# Desktop copilot tools schema
│   └── global_tools.json   # Global tools schema
└── data/
    ├── history.json        # Chat history storage
    ├── memory.txt          # User memory profile
    ├── logs.txt            # Application logs
    └── Shortcuts.md        # User shortcuts documentation
```

## 🔧 Core Components

### Classes
- **Config**: Manages application configuration and LLM client setup
- **Agent**: Handles AI agent functionality and tool management
- **History**: Tracks conversation history and message management

### Utils
Helper functions for:
- Configuration loading
- Datetime handling
- File I/O operations

### Functions
- **desktop_copilot.py**: Implements desktop agent that can see and control your computer for you. 

## 🎯 Key Features Explained

### Memory Consolidation
The system uses an advanced memory consolidation subsystem that:
- Reviews chat history
- Generates user profiles
- Maintains preferences and context
- Tracks ongoing tasks
- Stores user-related facts

### Screen Capture Integration
- Captures desktop screenshots
- Encodes images to base64
- Provides visual context to the AI model
- Configurable per monitor

## 🔐 Security

- Supports Local-only by default (127.0.0.1)
- API key configuration for LLM server access
- No external API calls required (local LLM)

## 🛠️ Development

### Adding Custom Tools
1. Define tool functions in `functions/<your-agent>.py` directory
2. Add tool schema to `tools_schema/<your-agent>.json` JSON files
3. Map tools in `main.py` using `tool_map`
4. Update requirements if needed

## 📝 Troubleshooting

**Connection Error**: Ensure LLM server is running on configured URL and port
**Screenshot Not Working**: Verify `primary_monitor` setting matches your display configuration
**Memory Issues**: Check `context_length` and `buffer_token` settings

## 📦 Dependencies Details

- **openai**: OpenAI-compatible Python SDK for LLM API calls
- **rich**: Terminal formatting and styling
- **mss**: Screen capture library
- **Wikipedia-API**: Wikipedia content retrieval
- **requests**: HTTP requests library

## 🚀 Performance Tips

- Adjust `context_length` based on your model's capabilities
- Reduce `keep_images` if memory usage is high or long processing time
- Use `buffer_token` to ensure response completion
- For low-end pc, use `qwen3.5-4b` local model with 16k context. Only requires 4GB VRAM.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and enhancement requests.

---