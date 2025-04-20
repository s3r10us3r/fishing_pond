import chess


class Coordinator:
    def __init__(self, moving, staying, board, gui):
        self.moving = moving
        self.staying = staying
        self.board = board
        self.gui = gui
        self.moving.update.connect(self.make_move)
        self.staying.update.connect(self.make_move)
        fen = self.board.fen()
        self.gui.load_fen(fen)

    def make_move(self, mv):
        self.board.push(mv)
        fen = self.board.fen()
        self.gui.load_fen(fen)
        self.gui.highlite_last_move(mv)
        self.moving, self.staying = self.staying, self.moving
        self.run()

    def run(self):
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            self.gui.end_game(f"Checkmate!\n\n{winner} wins.")
        elif self.board.is_stalemate():
            self.gui.end_game("Stalemate -- draw.")
        elif self.board.is_insufficient_material():
            self.gui.end_game("Draw -- insuficcient material")
        elif self.board.can_claim_fifty_moves():
            self.gui.end_game("Draw -- fifty-move rule.")
        elif self.board.can_claim_threefold_repetition():
            self.gui.end_game("Draw -- threefold repetition.")
        self.moving.start()
