# AI Chatbot

This is a simple AI chatbot application built with a Python backend and a vanilla HTML, CSS, and JavaScript frontend.

## 框架

### Backend

- **Python 3.9+**
- **FastAPI**: For building the RESTful API.
- **Uvicorn**: As the ASGI server to run FastAPI.
- **OpenAI API**: To generate AI responses.
- **Pydantic**: For data validation.
- **python-dotenv**: For managing environment variables.

### Frontend

- **HTML5**
- **CSS3**
- **JavaScript (ES6+)**: For client-side logic.

## 如何在本地运行

### Prerequisites

- Python 3.7 or newer.
- An API key from OpenAI.

### Backend Setup

1. **Navigate to the backend directory:**
   ```sh
   cd backend
   ```

2. **Create and activate a Conda environment:**
   ```sh
   conda create --name chatbot-env python=3.9 -y
   conda activate chatbot-env
   ```

3. **Install the required dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a file named `.env` in the `backend` directory by copying `env.example`.
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY='your_openai_api_key_here'
     ```

5. **Run the backend server:**
   ```sh
   python main.py
   ```
   The server will start on `http://localhost:8000`.

### Frontend Setup

1. **Open the `index.html` file:**
   - Navigate to the `frontend` directory.
   - Open the `index.html` file directly in your web browser.

You should now be able to interact with the chatbot in your browser.
