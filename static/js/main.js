console.log("main.js is loading!");
// Establish Socket.IO connection
const socket = io();

// We'll store the player's assigned role here: 'X', 'O', or 'spectator'
let myPlayer = null;
// We'll store the current game state (board, current_player, winner)
let gameState = null;

// On page load, create the board UI
window.addEventListener("DOMContentLoaded", () => {
  createBoard();
});

// ----------------------------
// Socket.IO Event Listeners
// ----------------------------

// 1. Player assignment (e.g., "You are player X")
socket.on("player_assignment", (data) => {
  myPlayer = data.player;
  updateStatus(`You are player: ${myPlayer}`);

  if (myPlayer === "spectator") {
    updateStatus("You are viewing as a spectator.");
  }
});

// 2. Receive the latest game state from the server
socket.on("game_state", (state) => {
  console.log("Received game_state:", state);
  gameState = state;
  updateBoard(state.board);
  handleGameState(state);
});

// 3. Display error messages from the server (e.g., invalid moves)
socket.on("error", (data) => {
  alert(data.message);
});

// 4. Start game event (when the second player joins)
socket.on("start_game", (data) => {
  updateStatus(data.message); // e.g., "The game starts!"
});

// 5. Waiting for opponent event (only one player in the room so far)
socket.on("waiting_for_opponent", (data) => {
  updateStatus(data.message); // e.g., "Waiting for your opponent..."
});

// ----------------------------
// DOM / Board Setup
// ----------------------------

// Create a 3×3 grid for Tic Tac Toe
function createBoard() {
  const boardDiv = document.getElementById("board");
  boardDiv.innerHTML = ""; // Clear any existing cells

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const cell = document.createElement("div");
      cell.classList.add("cell");
      cell.dataset.row = row;
      cell.dataset.col = col;
      cell.addEventListener("click", onCellClick);
      boardDiv.appendChild(cell);
    }
  }
}

// Update the board UI based on the 2D array from the server
function updateBoard(board) {
  const cells = document.querySelectorAll(".cell");
  cells.forEach(cell => {
    const row = parseInt(cell.dataset.row);
    const col = parseInt(cell.dataset.col);
    const value = board[row][col];
    cell.textContent = value;
    cell.classList.remove("X", "O"); // Remove old classes
    if (value === "X") {
      cell.classList.add("X");
    } else if (value === "O") {
      cell.classList.add("O");
    }
  });
}

// When a cell is clicked, attempt a move if it's valid
function onCellClick(e) {
  if (!gameState) return; // If we haven't received a game state yet, do nothing

  const row = parseInt(e.target.dataset.row);
  const col = parseInt(e.target.dataset.col);

  // Check if it's our turn and the game is not over
  if (myPlayer === gameState.current_player && !gameState.winner) {
    socket.emit("move", { row, col });
  }
}

// ----------------------------
// Handling Game State
// ----------------------------

function handleGameState(state) {
  console.log("handleGameState called. state =", state);
  console.log("myPlayer =", myPlayer);

  // 1. Check for a winner
  if (state.winner) {
    console.log("Winner detected:", state.winner);

    if (state.winner === myPlayer) {
      updateStatus("You Won!");
    } else if (myPlayer === "X" || myPlayer === "O") {
      updateStatus("You lost :(");
    } else {
      // spectator
      updateStatus(`Player ${state.winner} wins!`);
    }

    // Show both buttons
    document.getElementById("newGameBtn").style.display = "inline-block";
    document.getElementById("exitBtn").style.display = "inline-block";
    return;
  }

  // 2. Check for a draw (board is full, but no winner)
  if (isBoardFull(state.board)) {
    console.log("Board is full, checking for draw...");
    updateStatus("It's a draw!");

    // Show both buttons
    document.getElementById("newGameBtn").style.display = "inline-block";
    document.getElementById("exitBtn").style.display = "inline-block";
    return;
  }

  // 3. Otherwise, the game is ongoing
  console.log("No winner or draw. Current player =", state.current_player, "My player =", myPlayer);
  
  // Hide both buttons if the game is ongoing
  document.getElementById("newGameBtn").style.display = "none";
  document.getElementById("exitBtn").style.display = "none";

  if (myPlayer === state.current_player) {
    updateStatus("Your turn!");
  } else {
    updateStatus(`Waiting for player ${state.current_player}...`);
  }
}

// Helper function to check if the board is completely filled
function isBoardFull(board) {
  return board.every(row => row.every(cell => cell !== ""));
}

// ----------------------------
// Utility Functions
// ----------------------------
function updateStatus(msg) {
  const statusDiv = document.getElementById("status");
  if (statusDiv) {
    statusDiv.textContent = msg;
  }
}

const newGameBtn = document.getElementById("newGameBtn");
const exitBtn = document.getElementById("exitBtn");

// "New Game" button -> emit "reset_game"
newGameBtn.addEventListener("click", () => {
  console.log("New Game button clicked. Emitting 'reset_game'.");
  socket.emit("reset_game");
});

// "Exit" button -> redirect to /thanks
exitBtn.addEventListener("click", () => {
  console.log("Exit button clicked. Redirecting to /thanks.");
  window.location.href = "/thanks";
});