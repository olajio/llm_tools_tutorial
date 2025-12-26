"""
LLM Tools Tutorial: Airline Ticket Assistant
=============================================

This script demonstrates how to implement tools (function calling) 
in LLM applications. Features auto-pricing for unknown destinations.

Requirements:
    pip install openai gradio

Usage:
    export OPENAI_API_KEY="your-key"
    python ticket_assistant.py
"""

import sqlite3
import json
import random
import openai
import gradio as gr

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL = "gpt-4o-mini"  # Change to your preferred model
DB = "prices.db"

SYSTEM_MESSAGE = """You are a helpful airline ticket assistant. You can:
1. Look up ticket prices to various destinations
2. Set or update ticket prices when requested

When a price is not available for a city, one will be automatically generated and saved.
In such cases, advise the user that this is a newly added route and they should check back
later for potential price updates or promotions.

Always be friendly and helpful to customers."""


# =============================================================================
# DATABASE SETUP
# =============================================================================

def init_database():
    """Initialize the database with the prices table."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)'
        )
        conn.commit()


def seed_database():
    """Seed the database with initial prices."""
    initial_prices = {"london": 799, "paris": 899, "tokyo": 1420, "sydney": 2999}
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        for city, price in initial_prices.items():
            cursor.execute(
                'INSERT INTO prices (city, price) VALUES (?, ?) '
                'ON CONFLICT(city) DO UPDATE SET price = ?',
                (city, price, price)
            )
        conn.commit()


# =============================================================================
# TOOL FUNCTIONS
# =============================================================================

def generate_random_price():
    """Generate a random ticket price between $299 and $2999."""
    return round(random.uniform(299, 2999), 2)


def get_ticket_price(city):
    """
    Retrieve the ticket price for a given city.
    
    If the city doesn't exist, automatically generate a price,
    save it to the database, and flag it as newly added.
    """
    print(f"TOOL CALLED: get_ticket_price for '{city}'", flush=True)
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        result = cursor.fetchone()
        
        if result:
            return json.dumps({
                "status": "found",
                "city": city,
                "price": result[0],
                "message": f"The ticket price to {city} is ${result[0]:.2f}"
            })
        else:
            # Auto-generate and save price for new city
            new_price = generate_random_price()
            cursor.execute(
                'INSERT INTO prices (city, price) VALUES (?, ?)',
                (city.lower(), new_price)
            )
            conn.commit()
            print(f"AUTO-GENERATED: New price for '{city}': ${new_price}", flush=True)
            
            return json.dumps({
                "status": "newly_added",
                "city": city,
                "price": new_price,
                "message": (
                    f"The ticket price to {city} is ${new_price:.2f}. "
                    "This is a newly added route - please check back later "
                    "for potential price updates or promotions."
                )
            })


def set_ticket_price(city, price):
    """Set or update the ticket price for a given city."""
    print(f"TOOL CALLED: set_ticket_price for '{city}' at ${price}", flush=True)
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO prices (city, price) VALUES (?, ?) '
            'ON CONFLICT(city) DO UPDATE SET price = ?',
            (city.lower(), price, price)
        )
        conn.commit()
    
    return json.dumps({
        "status": "success",
        "city": city,
        "price": price,
        "message": f"Successfully set the ticket price to {city} to ${price:.2f}"
    })


# =============================================================================
# TOOL DEFINITIONS (JSON Schemas for the LLM)
# =============================================================================

GET_PRICE_FUNCTION = {
    "name": "get_ticket_price",
    "description": (
        "Get the price of a return ticket to the destination city. "
        "If the city doesn't have a price yet, one will be automatically "
        "generated and saved. The response includes a 'status' field: "
        "'found' for existing prices, 'newly_added' for auto-generated prices. "
        "For newly added routes, advise the user to check back for updates."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

SET_PRICE_FUNCTION = {
    "name": "set_ticket_price",
    "description": "Set or update the price of a return ticket to a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city to set the ticket price for",
            },
            "price": {
                "type": "number",
                "description": "The new price for the ticket in dollars",
            },
        },
        "required": ["destination_city", "price"],
        "additionalProperties": False
    }
}

# Register tools
TOOLS = [
    {"type": "function", "function": GET_PRICE_FUNCTION},
    {"type": "function", "function": SET_PRICE_FUNCTION}
]


# =============================================================================
# TOOL HANDLER
# =============================================================================

def handle_tool_calls(message):
    """Process all tool calls from the LLM's response."""
    responses = []
    
    for tool_call in message.tool_calls:
        arguments = json.loads(tool_call.function.arguments)
        
        if tool_call.function.name == "get_ticket_price":
            city = arguments.get('destination_city')
            result = get_ticket_price(city)
        
        elif tool_call.function.name == "set_ticket_price":
            city = arguments.get('destination_city')
            price = arguments.get('price')
            result = set_ticket_price(city, price)
        
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_call.function.name}"})
        
        responses.append({
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call.id
        })
    
    return responses


# =============================================================================
# CHAT FUNCTION
# =============================================================================

def chat(message, history):
    """Process a chat message, handling any tool calls the LLM makes."""
    # Build message history
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = (
        [{"role": "system", "content": SYSTEM_MESSAGE}] 
        + history 
        + [{"role": "user", "content": message}]
    )
    
    # Get initial response
    response = openai.chat.completions.create(
        model=MODEL, 
        messages=messages, 
        tools=TOOLS
    )
    
    # Process tool calls until done
    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        tool_responses = handle_tool_calls(assistant_message)
        
        messages.append(assistant_message)
        messages.extend(tool_responses)
        
        response = openai.chat.completions.create(
            model=MODEL, 
            messages=messages, 
            tools=TOOLS
        )
    
    return response.choices[0].message.content


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    seed_database()
    print("Database ready!")
    print("\nLaunching Gradio interface...")
    print("Try asking: 'What's the price to London?' or 'How much to Dubai?'\n")
    
    gr.ChatInterface(fn=chat, type="messages").launch()
