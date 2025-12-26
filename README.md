# LLM Tools Tutorial: Building an Airline Ticket Assistant

A comprehensive tutorial demonstrating how to implement **tools** (function calling) in LLM applications using OpenAI's API, with a practical airline ticket pricing chatbot.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)
![Gradio](https://img.shields.io/badge/Gradio-Chat%20Interface-orange.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)

## 🎯 What You'll Learn

- **What are LLM tools?** How to extend language models beyond text generation
- **Tool definitions**: Creating JSON schemas that describe your functions
- **Tool handlers**: Executing functions when the LLM requests them
- **Conversation loops**: Managing multi-turn tool interactions
- **Database integration**: Persistent storage with SQLite
- **Auto-pricing feature**: Dynamically generating and saving prices for new destinations

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│   Gradio    │────▶│   OpenAI    │
│   Message   │     │  Interface  │     │     LLM     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                           Tool Call Request   │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SQLite    │◀────│    Tool     │◀────│    Tool     │
│  Database   │     │  Functions  │     │   Handler   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Get Ticket Price** | Look up prices for any destination |
| **Set Ticket Price** | Manually update or create prices |
| **Auto-Pricing** | Unknown cities automatically get prices generated and saved |
| **Persistent Storage** | All prices stored in SQLite database |
| **Chat Interface** | User-friendly Gradio web interface |

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/llm-tools-tutorial.git
   cd llm-tools-tutorial
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install openai gradio
   ```

4. **Set your OpenAI API key**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   Or in Python:
   ```python
   import openai
   openai.api_key = "your-api-key-here"
   ```

## 🎮 Usage

### Running the Notebook

1. Start Jupyter:
   ```bash
   jupyter notebook llm_tools_tutorial.ipynb
   ```

2. Run all cells to launch the Gradio interface

3. Try these example prompts:
   - "What's the ticket price to Paris?"
   - "How much for a flight to Dubai?" *(auto-generates price)*
   - "Set the price to Berlin to $550"

### Running as a Script

You can also extract the code and run it directly:

```python
python ticket_assistant.py
```

## 📖 How It Works

### 1. Tool Definition

Tools are defined as JSON schemas that tell the LLM what functions are available:

```python
get_price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
    }
}
```

### 2. Tool Execution

When the LLM wants to use a tool, it returns a `tool_calls` response. Our handler executes the actual function:

```python
def handle_tool_calls(message):
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_ticket_price":
            city = json.loads(tool_call.function.arguments)["destination_city"]
            result = get_ticket_price(city)
            # Return result to LLM
```

### 3. Auto-Pricing Logic

When a city isn't found, the system automatically:
1. Generates a random price ($299-$2999)
2. Saves it to the database
3. Returns with a "newly_added" status
4. Advises user to check back for updates

```python
if not result:
    new_price = generate_random_price()
    save_to_database(city, new_price)
    return {"status": "newly_added", "price": new_price}
```

## 📁 Project Structure

```
llm-tools-tutorial/
├── README.md                    # This file
├── llm_tools_tutorial.ipynb     # Main tutorial notebook
├── prices.db                    # SQLite database (auto-created)
└── requirements.txt             # Python dependencies
```

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `DB` | `prices.db` | SQLite database file path |

## 📊 Database Schema

```sql
CREATE TABLE prices (
    city TEXT PRIMARY KEY,
    price REAL
);
```

## 🧪 Example Interactions

**Existing City:**
```
User: What's the price to London?
Assistant: The ticket price to London is $799.00.
```

**New City (Auto-Pricing):**
```
User: How much to fly to Dubai?
Assistant: The ticket price to Dubai is $1,547.32. This is a newly 
           added route - please check back later for potential 
           price updates or promotions!
```

**Same City Again:**
```
User: What about Dubai again?
Assistant: The ticket price to Dubai is $1,547.32.
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for the API and function calling feature
- [Gradio](https://gradio.app/) for the easy-to-use chat interface
- Inspired by LLM engineering best practices

---

**Happy Learning! 🚀**

If you found this tutorial helpful, please give it a ⭐ on GitHub!
