# UniTLServer

Host your own Flask server locally to translate text from Unity games via [XUnity-Auto-Translator](https://github.com/bbepis/XUnity.AutoTranslator) using a modern LLM (Gemini 2.5 Flash, DeepSeek, or any OpenAI‑compatible API).

I made this because the default translators often produce unnatural or broken text that fries your brain.

## Supported Providers

The server can use either of these backends (choose at startup):

| Provider               | Model                   | API Key                     |
| ---------------------- | ----------------------- | --------------------------- |
| **OpenRouter** (default) | `google/gemini-2.5-flash` | `OPENROUTER_API_KEY`        |
| **DeepSeek**           | `deepseek-chat`         | `DEEPSEEK_API_KEY`          |

You can also override the model via the command line. The underlying HTTP endpoints remain exactly the same, so XUnity‑Auto‑Translator doesn’t need any changes.

---

## How to Run

### 1. Get an API key

- **OpenRouter** (Gemini): Get your key from [openrouter.ai/keys](https://openrouter.ai/keys)
- **DeepSeek**: Get your key from [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)

### 2. Provide the key to the server

The server checks for the key in this order:

1. `--api-key` command‑line argument
2. Environment variable (e.g. `OPENROUTER_API_KEY` or `DEEPSEEK_API_KEY`)
3. A `secrets.json` file in the same directory (optional fallback)

#### Option A: Environment variable (recommended)

```bash
# For OpenRouter (default)
export OPENROUTER_API_KEY="your-key-here"

# Or for DeepSeek
export DEEPSEEK_API_KEY="your-key-here"
```

#### Option B: secrets.json (fallback)

Create `secrets.json` with the appropriate key:

```json
{
  "OPENROUTER_API_KEY": "your-key-here"
}
```

(If using DeepSeek, put `"DEEPSEEK_API_KEY"` instead.)

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

Choose your provider and model (defaults are shown). The server will exit immediately if no API key is found.

```bash
# Default: OpenRouter + Gemini 2.5 Flash
python main.py

# DeepSeek
python main.py --provider deepseek

# Custom model (must be compatible with the chosen provider)
python main.py --provider openrouter --model google/gemini-2.5-pro
```

The server runs at `http://127.0.0.1:5000`.

### 5. Configure XUnity‑Auto‑Translator

Edit your game’s `AutoTranslator.ini` (or `Config.ini`):

```ini
[Custom]
Url=http://127.0.0.1:5000/translate
```

### 6. Play

- Launch the game with the XUnity‑Auto‑Translator plugin enabled.
- Press **ALT+0** to open the plugin menu.
- Change the translator to **Custom**.

The game will now use your chosen LLM for translation.

---

## Endpoints (unchanged)

| Method | Endpoint          | Usage                                                               |
| ------ | ----------------- | ------------------------------------------------------------------- |
| GET    | `/translate`      | `?text=こんにちは&lang=en&source=ja` → translated text              |
| GET    | `/models`         | Returns the active provider and model info                          |
| POST   | `/translate/stream` | Streaming endpoint (work in progress)                            |

The `source` parameter defaults to `ja` (Japanese). Supported languages: `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de`.

---

## Notes

- The server uses the OpenAI‑compatible chat completions API, so it can be extended to other providers easily.
- Streaming is not yet implemented, but the current endpoint responds quickly enough for real‑time game translation.
- If you’re behind a proxy or need custom headers, modify the `PROVIDER_CONFIG` in `main.py`.

---

## Troubleshooting

- **“No API key found” error**: Make sure you set the correct environment variable or `secrets.json` entry for your chosen provider.
- **Translation returns an error**: Check that your API key is valid and you have credits/quota. You can also try lowering `temperature` in the script.
