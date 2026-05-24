from flask import Flask, request, jsonify, Response
import json
import os
import re
import requests
import argparse
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Command‑line argument parsing (at startup, before any request)
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Translation Server with multiple LLM backends"
)
parser.add_argument(
    "--provider",
    choices=["openrouter", "deepseek"],
    default="openrouter",
    help="Which API provider to use (default: openrouter)",
)
parser.add_argument(
    "--model",
    default=None,
    help="Override the default model name for the chosen provider",
)
parser.add_argument(
    "--api-key",
    default=None,
    help="API key for the provider (can also be set via env var or secrets.json)",
)
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------
PROVIDER_CONFIG = {
    "openrouter": {
        "api_base": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-2.5-flash",
        "env_key_name": "OPENROUTER_API_KEY",
        "extra_headers": {
            "HTTP-Referer": "http://127.0.0.1:5000",
            "X-Title": "Gemini OpenRouter Translator",
        },
    },
    "deepseek": {
        "api_base": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "env_key_name": "DEEPSEEK_API_KEY",
        "extra_headers": {},
    },
}

provider = args.provider
config = PROVIDER_CONFIG[provider]

# Determine the model
model = args.model if args.model else config["default_model"]

# Resolve API key: command line > environment variable > secrets.json fallback
API_KEY = args.api_key
if not API_KEY:
    API_KEY = os.environ.get(config["env_key_name"])

if not API_KEY:
    # Fallback to secrets.json (check both possible keys)
    try:
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
            API_KEY = secrets.get(config["env_key_name"]) or secrets.get(
                "GEMINI_API_KEY"
            )
    except Exception:
        pass

if not API_KEY:
    print(
        f"ERROR: No API key found for provider '{provider}'."
        f" Please set {config['env_key_name']} or provide --api-key."
    )
    sys.exit(1)

# Common headers for API requests
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    **config["extra_headers"],
}


# ---------------------------------------------------------------------------
# Translation prompt (unchanged)
# ---------------------------------------------------------------------------
def create_translation_prompt(text, target_lang="en", source_lang="ja"):
    lang_names = {
        "zh": "Chinese",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
    }
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    return f"""You are a professional {source_name}-to-{target_name} translator.
        Retain honorifics.
        Preserve tone, emotion and nuances when possible.
        You must return the result only.

        Translate the following {source_name} text into natural {target_name}:
        {text}"""


# ---------------------------------------------------------------------------
# Core translation function (no HTTP parameter changes)
# ---------------------------------------------------------------------------
def call_translation_api(prompt):
    """Calls the selected provider's chat completions endpoint."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
    }
    url = f"{config['api_base']}/chat/completions"
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()

    if not data.get("choices"):
        error_message = data.get("error", {}).get("message", "No choices in response")
        raise Exception(f"API error: {error_message}")

    return data["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Routes (unchanged signatures)
# ---------------------------------------------------------------------------
@app.route("/translate", methods=["GET"])
def translate():
    try:
        text = request.args.get("text", "").strip()
        target_lang = request.args.get("lang", "en")
        source_lang = request.args.get("source", "ja")

        if not text:
            return "No text provided", 400

        prompt = create_translation_prompt(text, target_lang, source_lang)
        translation = call_translation_api(prompt)
        # Clean markers just in case
        translation = re.sub(r"<Start>|<End>", "", translation).strip()
        return translation

    except requests.exceptions.RequestException as e:
        return f"Error communicating with API: {e}", 500
    except Exception as e:
        return f"An unexpected error occurred: {e}", 500


@app.route("/translate/stream", methods=["POST"])
def translate_stream():
    return "Streaming endpoint is WIP (can be implemented for both providers).", 501


@app.route("/models", methods=["GET"])
def get_models():
    return jsonify(
        {
            "models": [
                {
                    "id": model,
                    "name": f"{provider.capitalize()} - {model}",
                    "description": f"Active model via {provider} API",
                    "version": model,
                }
            ]
        }
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Startup info
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(
        f"🚀 Starting Translation Server using {provider.upper()} API (model: {model})"
    )
    print("📋 Endpoints:")
    print("  GET /translate - Standard translation")
    print("  POST /translate/stream - Streaming (WIP)")
    print("  GET /models - Active model info")
    print()
    print("💡 Example:")
    print("  curl 'http://127.0.0.1:5000/translate?text=こんにちは&lang=en'")
    print()
    app.run(host="127.0.0.1", port=5000, debug=True)
