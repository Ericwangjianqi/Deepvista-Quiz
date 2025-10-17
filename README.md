# AI Chatbot

This is a simple AI chatbot application built with a Python backend and a vanilla HTML, CSS, and JavaScript frontend.

A Demo for this project:
https://youtu.be/xFoziKcxuvg

## Framework

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

## How to Run Locally

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

---

## AI Coder Usage Declaration

This project was developed with the assistance of an AI coding tool.

- **Tool Used:** Cursor
- **Prompt Record:**
  - *(copy of the project description), What framework do I need to build to complete such a project, and what are the specific functions of each file*
  - *What parts do I need to implement for main.py in the backend folder, and what libraries do I need to use?*
  - *Please help me build a website using HTML in the frontend folder. The website should have a dialogue box between the user and AI, an input area for the user, a send button for clicking, and the ability to see messages sent by the user and AI replies. The design style should be simple and aesthetically pleasing*
  - *To achieve the connection between the frontend and backend, list the functions I need to implement in script.js*




