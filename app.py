from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# ----------------------------
# Tic Tac Toe Game Logic Class
# ----------------------------
class Game:
    def __init__(self):
        self.reset_game()
    
    def reset_game(self):
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_player = None
        self.winner = None


    def make_move(self, row, col):
        # Check if cell is empty and no winner yet
        if self.board[row][col] == '' and self.winner is None:
            self.board[row][col] = self.current_player
            print(f"DEBUG: make_move called - row={row}, col={col}, player={self.current_player}")

            if self.check_win(row, col):
                self.winner = self.current_player
                print(f"DEBUG: Winner set to {self.winner}")
            else:
                # Switch turn
                self.current_player = 'O' if self.current_player == 'X' else 'X'

            return True

        print("DEBUG: Invalid move or winner already set.")
        return False  # Simply return False without checking for win again

    def check_win(self, row, col):
        b = self.board
        p = self.current_player

        # Check row
        if all(b[row][c] == p for c in range(3)):
            return True
        # Check column
        if all(b[r][col] == p for r in range(3)):
            return True
        # Check main diagonal
        if row == col and all(b[i][i] == p for i in range(3)):
            return True
        # Check anti-diagonal
        if row + col == 2 and all(b[i][2 - i] == p for i in range(3)):
            return True
        return False

# ----------------------------
# Flask Application Setup
# ----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# ----------------------------
# Data Structures
# ----------------------------
# We'll store multiple game rooms in a dict: { room_id: {...} }
# Each entry can have:
#   "game": a Game() instance
#   "players": { sid_of_playerX: "X", sid_of_playerO: "O" }
#   "slots": {"X": None or sid, "O": None or sid}
#   "status": "waiting" or "in_progress"
rooms = {}

# Keep track of which room a particular sid (socket ID) is in.
#   sid_room_map[sid] = room_id
sid_room_map = {}

# ----------------------------
# Routes
# ----------------------------

@app.route('/')
def welcome():
    """
    This is the 'welcome' page. 
    In practice, you'd render a template like welcome.html, 
    showing options: 
       - "Create a new game" (choose X or O)
       - "Join an existing game" (if there's a waiting game)
    """
    return render_template('welcome.html')

@app.route('/create_game/<role>')
def create_game(role):
    """
    Create a new game room with a unique room_id.
    The first player picks X or O. The other slot is open.
    Redirect the user to /game/<room_id> so they can connect via Socket.IO.
    """
    room_id = str(uuid.uuid4())
    rooms[room_id] = {
        "game": Game(),
        "players": {},      # We'll fill this once they connect via Socket
        "slots": {"X": None, "O": None},
        "status": "waiting"
    }
    # We'll store the chosen role in the URL or session so that 
    # the user is assigned that role upon Socket.IO connect.
    return redirect(url_for('game_page', room_id=room_id, chosen_role=role))

@app.route('/join_game/<room_id>')
def join_game(room_id):
    """
    If there's a waiting room with an open slot, let the user join as the remaining role.
    If the game is full or doesn't exist, you might show an error or redirect to welcome.
    """
    if room_id not in rooms:
        return render_template('welcome.html', error="Invalid game ID. Please try again.")
    # For simplicity, assume there's exactly one open slot in that room
    return redirect(url_for('game_page', room_id=room_id, chosen_role='auto'))


@app.route('/game/<room_id>')
def game_page(room_id):
    # (Optional) Check if this room exists; if not, redirect or show an error
    if room_id not in rooms:
        return redirect(url_for('welcome'))  # or render a 404 page

    # Pass room_id to the template
    return render_template('index.html', room_id=room_id)

@app.route('/thanks')
def thanks():
    """
    Renders a simple "Thanks for playing" page.
    This is where players go if they choose NOT to play again.
    """
    return render_template('thanks.html')


# ----------------------------
# Socket.IO Event Handlers
# ----------------------------
@socketio.on('connect')
def on_connect():
    """
    This fires whenever a new socket connects.
    We'll check if they're arriving via /game/<room_id>?chosen_role=???
    Then we assign them to that room, set their role, etc.
    """
    sid = request.sid
    # Extract the room_id and chosen_role from the request URL.
    # The Referer header is used as a fallback but may be missing in some cases.
    ref = request.headers.get("Referer", "")  # e.g., "http://localhost:5000/game/<room_id>?chosen_role=X"
    
    # Parse out the room_id and chosen_role from the URL
    # This is a simplistic approach; you might want to parse query params more robustly
    room_id = None
    chosen_role = None

    # Example: if the referer has "game/1234-uuid?chosen_role=X"
    # We can do something like:
    import urllib.parse
    parsed = urllib.parse.urlparse(ref)
    query_params = urllib.parse.parse_qs(parsed.query)
    chosen_role_list = query_params.get('chosen_role', [])
    if chosen_role_list:
        chosen_role = chosen_role_list[0]  # e.g. "X", "O", or "auto"

    # Also parse the path for the room_id
    path_parts = parsed.path.split('/')
    if len(path_parts) >= 3 and path_parts[-2] == 'game':
        room_id = path_parts[-1]  # The last part of the path

    if not room_id or room_id not in rooms:
        # If we can't figure out the room, or it doesn't exist, disconnect
        print(f"No valid room found for sid={sid}")
        return

    # Join the Socket.IO room so we can broadcast to just this game
    join_room(room_id)
    sid_room_map[sid] = room_id

    room_data = rooms[room_id]
    game_obj = room_data["game"]

    # If the room is "waiting", we need to assign the new player's role
    # If the chosen_role is "X" or "O" (and it's free), assign it
    # If chosen_role = "auto", assign whichever is free
    # If both slots are filled, they can't join => (in a real app, handle as error or spectator)
    assigned_role = None

    if room_data["status"] == "waiting":
        if chosen_role in ["X", "O"]:
            # Try to assign chosen_role if it's not taken
            if room_data["slots"][chosen_role] is None:
                room_data["slots"][chosen_role] = sid
                assigned_role = chosen_role
            else:
                # The chosen slot is already taken, so try the other
                other = "O" if chosen_role == "X" else "X"
                if room_data["slots"][other] is None:
                    room_data["slots"][other] = sid
                    assigned_role = other
        else:
            # chosen_role = 'auto' => pick whichever is free
            if room_data["slots"]["X"] is None:
                room_data["slots"]["X"] = sid
                assigned_role = "X"
            elif room_data["slots"]["O"] is None:
                room_data["slots"]["O"] = sid
                assigned_role = "O"

        # Mark in room_data["players"]
        if assigned_role:
            room_data["players"][sid] = assigned_role

            # Count how many slots are filled
            filled_slots = sum(1 for r in ["X", "O"] if room_data["slots"][r] is not None)

            if filled_slots == 1:
                room_data["first_player"] = assigned_role
                # Also set the game’s current_player right away:
                game_obj.current_player = assigned_role
                # Only one player so far => broadcast a "waiting_for_opponent" event
                socketio.emit('waiting_for_opponent', {
                    "message": "Waiting for your opponent..."
                }, room=room_id)

            elif filled_slots == 2:
                # Both slots now filled => game in progress
                room_data["status"] = "in_progress"
                socketio.emit('start_game', {"message": "The game starts!"}, room=room_id)
        else:
            # No slot was assigned => 3rd user => spectator
            room_data["players"][sid] = "spectator"
            assigned_role = "spectator"
    else:
        # If the room is already in_progress
        # Either we have a 3rd user => spectator
        assigned_role = "spectator"
        room_data["players"][sid] = "spectator"

    print(f"Client connected: sid={sid}, assigned={assigned_role}, room={room_id}")

    # Tell this user what role they got
    emit('player_assignment', {'player': assigned_role}, room=sid)

    # Send the current board state
    emit_game_state(room_id)


@socketio.on('move')
def handle_move(data):
    sid = request.sid
    row = data.get('row')
    col = data.get('col')

    # Find which room this sid is in
    room_id = sid_room_map.get(sid)
    if not room_id or room_id not in rooms:
        emit('error', {'message': 'Invalid room or not in a game.'}, room=sid)
        return

    room_data = rooms[room_id]
    game_obj = room_data["game"]
    player_role = room_data["players"].get(sid, "spectator")

    # Check if it's a valid move
    if player_role in ['X', 'O'] and player_role == game_obj.current_player:
        # Check if the cell is already occupied
        if game_obj.board[row][col] != '':
            emit('error', {
                'message': "Cell occupied! Choose another."
            }, room=sid)
            return

        # Make the move
        valid = game_obj.make_move(row, col)
        if valid:
            emit_game_state(room_id)
        else:
            emit('error', {'message': 'Invalid move.'}, room=sid)
    else:
        emit('error', {'message': 'Not your turn or invalid player.'}, room=sid)


@socketio.on('reset_game')
def handle_reset_game():
    sid = request.sid
    room_id = sid_room_map.get(sid)
    if not room_id or room_id not in rooms:
        return

    room_data = rooms[room_id]
    game_obj = room_data["game"]
    game_obj.reset_game()
    
    # Restore the first player after reset, ensuring turn order is preserved.
    if "first_player" in room_data:
        game_obj.current_player = room_data["first_player"]

    emit_game_state(room_id)



@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    room_id = sid_room_map.get(sid)
    print(f"Client disconnected: {sid}")

    if room_id in rooms:
        room_data = rooms[room_id]
        # Remove from players
        if sid in room_data["players"]:
            role = room_data["players"][sid]
            del room_data["players"][sid]
            # Also free up the slot if it was X or O
            if role in ["X", "O"]:
                room_data["slots"][role] = None
        # Remove from sid_room_map
        del sid_room_map[sid]

        # Optionally, if both players leave or the room is empty, you can delete the room
        # For now, let's keep it.


# ----------------------------
# Helper Functions
# ----------------------------
def emit_game_state(room_id):
    print(f"DEBUG: Inside emit_game_state for room={room_id}")
    if room_id not in rooms:
        print(f"DEBUG: room_id={room_id} not in rooms; returning early.")
        return

    room_data = rooms[room_id]
    game_obj = room_data["game"]
    
    payload = {
        'board': game_obj.board,
        'current_player': game_obj.current_player,
        'winner': game_obj.winner
    }

    print(f"DEBUG: Emitting game_state with winner = {game_obj.winner}")
    socketio.emit('game_state', payload, room=room_id)



# ----------------------------
# Run the Application
# ----------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True)
