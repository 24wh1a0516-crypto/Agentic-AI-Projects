# multimodel-app

## Setup

1. Create and activate the virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env` and add your API key:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

## Run

```bash
python main.py
```
