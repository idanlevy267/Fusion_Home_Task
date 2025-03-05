# Tic Tac Toe Project README

## Overview
This repository contains a real-time Tic Tac Toe (X and O) game implemented within a 5-hour time frame. It enables two players to play simultaneously, with moves updated in real time via WebSockets (Flask-SocketIO). A player's move is instantly visible on the opponent’s browser. The backend is built with Python (Flask and Flask-SocketIO), while the frontend uses simple HTML, CSS, and JavaScript.

## Implementation Details

### Backend
- A **Flask** server with **Flask-SocketIO** tracks multiple game rooms. Each room has a `Game` instance that:
  - Manages a **3x3 board** stored as a list of lists.
  - Tracks the **current player** (X or O).
  - Checks for a **win condition** after each move.
  - Prevents invalid moves and enforces turn-based play.

### Frontend
- The board is displayed using **HTML, CSS, and JavaScript**.
- **Socket.IO** enables real-time updates between players.

## Project Structure

- **`app.py`**: Main server logic
  - Manages game state, player moves, and WebSocket events.
  - Handles multiple game rooms and enforces game rules.

- **Frontend (`templates/` and `static/`)**:
  - `welcome.html`: Start page (create or join a game).
  - `index.html`: Tic Tac Toe board UI with real-time updates.
  - `thanks.html`: Simple exit page.
  - `main.js`: Handles UI updates and player actions via WebSockets.
  - `styles.css`: Provides a clean, grid-based layout for the board.

## Basic Flow
1. A user visits the **welcome page** and can:
   - **Create a new game**, selecting X or O.
   - **Join an existing game** using a game ID.
2. The first player is assigned their chosen **role (X or O)**. The second player automatically gets the other role.
3. The **board updates in real-time** using Socket.IO.
4. The server checks for a **win condition** or **draw** after each move.
5. Once the game ends:
   - Players see **"You Won!"**, **"You lost :("**, or **"It's a draw!"**.
   - They can choose to **start a new game** or **exit**.

## Win Condition
A player wins if they have **three marks in a row**, **column**, or **diagonal**:
- **Rows**: All three cells in a row contain the same mark.
- **Columns**: All three cells in a column contain the same mark.
- **Diagonals**: The main or anti-diagonal contains the same mark.

If all cells are filled with no winner, the game results in a **draw**.

## Instructions to Run

1. Clone this repository locally: git clone <repo-url> cd <repo-folder>
2. Install dependencies: pip install -r requirements.txt
3. Run the server: python app.py
4. Open a browser and go to: http://localhost:5000
5. Create a game or join an existing one.
6. Open two browsers (or an incognito window) to play.

## Testing the Game
- **Server Startup**: Run `python app.py` and ensure no errors occur.
- **Player Connection**: Create a new game, join from another browser, and verify moves sync in real-time.
- **Win Condition**: Force three in a row and confirm the correct player is declared the winner.
- **Draw Condition**: Fill the board without a winner and check if "It's a draw!" appears.
- **Game Reset**: Click "New Game" and verify the board resets.

## Entities and Responsibilities
- **`Game` class**: Manages the board, current player, and win condition checks.
- **Flask-SocketIO**: Ensures real-time updates.
- **Client-side (`main.js`)**: Renders the board, processes player moves, and handles game state updates.

## AI Assistance
AI assistance was used for architectural guidance, code snippets, and best practices. However, all final implementation was manually reviewed, debugged, and refined within the 5-hour timeframe to ensure efficiency, readability, and maintainability.

