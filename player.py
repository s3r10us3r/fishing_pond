import time

import chess
from PyQt5.QtCore import QThread, pyqtSignal


class Player(QThread):
    update = pyqtSignal(object)

    def __init__(self, pieces, board):
        self.pieces = pieces
        self.board = board
        self.chosen_move = None
        super().__init__()

    def run(self):
        for row in self.pieces:
            for piece in row:
                if piece is not None:
                    piece.set_callback(lambda m: self.__choose_move(m))
                    piece.clear_moves()

        moves = list(self.board.legal_moves)
        for move in moves:
            for row in self.pieces:
                for piece in row:
                    if piece is not None and piece.get_square() == move.from_square:
                        piece.load_move(move)

        while self.chosen_move is None:
            time.sleep(0.01)
        mv = self.chosen_move
        self.chosen_move = None
        self.update.emit(mv)

    def __choose_move(self, move):
        self.chosen_move = move


class Engine(QThread):
    update = pyqtSignal(object)

    def __init__(self, board, engine):
        self.engine = engine
        self.board = board
        super().__init__()

    def run(self):
        result = self.engine.play(self.board, chess.engine.Limit(depth=5))
        move = result.move
        self.update.emit(move)
