import math

import chess
from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QFrame,
                             QGraphicsPixmapItem, QGraphicsRectItem,
                             QGraphicsScene, QGridLayout, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)


def load_piece_dict():
    pieces = ["p", "n", "b", "r", "q", "k", "P", "N", "B", "R", "Q", "K"]
    res_dict = {}
    for piece in pieces:
        color_c = "b" if piece.islower() else "w"
        piece_c = piece.upper()
        path = "pieces/" + color_c + piece_c + ".svg"
        pixmap = QPixmap(path)
        res_dict[piece] = pixmap
    return res_dict


class ChessPiece(QGraphicsPixmapItem):
    def __init__(self, pixmap, board, row, col, color):
        super().__init__(pixmap, None)
        self.color = color
        self.setTransformationMode(Qt.SmoothTransformation)
        self.piece_dict = load_piece_dict()
        self.board = board
        self.moves = []
        self.curr_pos = (row, col)
        self.set_square(row, col)

    def load_move(self, move):
        self.setFlags(QGraphicsPixmapItem.ItemIsMovable)
        self.moves.append(move)

    def targets(self):
        return [mv.to_square for mv in self.moves]

    def mousePressEvent(self, event):
        self.board.highlite_squares(self.targets())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.board.lowlite_squares(self.targets())
        new_pos = self.pos()
        col = normalize_position(new_pos.x(), self.board.square_width)
        row = normalize_position(new_pos.y(), self.board.square_height)
        for mv in self.moves:
            m_row, m_col = (7 - mv.to_square // 8, mv.to_square % 8)
            if m_row == row and m_col == col:
                mv = (
                    self.get_promotion_mv(mv.from_square, mv.to_square)
                    if mv.promotion is not None
                    else mv
                )
                self.curr_pos = (row, col)
                self.callback(mv)
                return
        self.set_square(self.curr_pos[0], self.curr_pos[1])

    def clear_moves(self):
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, False)
        self.moves = []

    def set_callback(self, fn):
        self.callback = fn

    def set_square(self, row, col):
        w = self.board.square_width
        h = self.board.square_height
        self.setPos(col * w, row * h)

    def get_promotion_mv(self, start, target):
        prom_choice = choose_promotion(self.color)
        if prom_choice is not None:
            piece, ch = prom_choice
            move = chess.Move(start, target, promotion=piece)
            move.ch = ch
        return move

    def get_square(self):
        row, col = self.curr_pos
        return (7 - row) * 8 + col


def normalize_position(pos, div):
    pos = round(pos, -2) // div
    pos = max(min(pos, 7), 0)
    return int(pos)


class GuiBoard(QGraphicsScene):
    def __init__(self, width, height, super_board, engine):
        super().__init__()
        self.moving = "player"
        self.staying = "engine"
        self.width = width
        self.height = height
        self.square_height = height // 8
        self.square_width = width // 8
        self.engine = engine
        self.pieces = [[None for _ in range(8)] for _ in range(8)]

        self._load_piece_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        self.piece_dict = load_piece_dict()
        self._render_squares()
        self._render_pieces()
        self.super_board = super_board
        self.last_move = None

    def _render_squares(self):
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                color = "white" if (row + col) % 2 == 0 else "#61262a"
                brush = QBrush(QColor(color))
                rect = QGraphicsRectItem(
                    col * self.square_width,
                    row * self.square_height,
                    self.square_width,
                    self.square_height,
                )
                rect.setBrush(brush)
                self.addItem(rect)
                self.squares[row][col] = rect

    def load_fen(self, fen):
        piece_fen = fen.split(" ")[0]
        self._load_piece_fen(piece_fen)
        self._render_pieces()

    def _load_piece_fen(self, fen):
        self.piece_squares = [[" " for _ in range(8)] for _ in range(8)]
        ranks = fen.split("/")
        pieces_str = "pnbrqk"
        for row, rank in enumerate(ranks):
            col = 0
            for c in rank:
                if c.lower() in pieces_str:
                    self.piece_squares[row][col] = c
                    col += 1
                else:
                    skip = int(c)
                    col += skip

    def _render_pieces(self):
        self.pieces = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                piece = self.piece_squares[row][col]
                if piece == " ":
                    continue
                pixmap = self.piece_dict[piece]
                scaled = pixmap.scaled(
                    self.width // 8,
                    self.height // 8,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                color = "w" if piece.isupper() else "b"
                piece = ChessPiece(scaled, self, row, col, color)
                self.addItem(piece)
                self.pieces[row][col] = piece

    def _clear_pieces(self):
        for row in self.pieces:
            for piece in self.pieces:
                if piece is not None:
                    self.removeItem(piece)
        self.pieces = [[None for _ in range(8)] for _ in range(8)]

    def load_moves(self, moves):
        for mv in moves:
            (row, col) = (7 - mv.from_square // 8, mv.from_square % 8)
            self.pieces[row][col].load_move(mv)

    def highlite_squares(self, squares):
        for sq in squares:
            (row, col) = (7 - sq // 8, sq % 8)
            color = "pink" if (row + col) % 2 == 0 else "red"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)

    def lowlite_squares(self, squares):
        for sq in squares:
            (row, col) = (7 - sq // 8, sq % 8)
            color = "white" if (row + col) % 2 == 0 else "#61262a"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)

    def clear_moves(self):
        for row in range(0, 8):
            for col in range(0, 8):
                if self.pieces[row][col]:
                    self.pieces[row][col].clear_moves()

    def del_piece(self, row, col):
        piece = self.pieces[row][col]
        self.removeItem(piece)
        self.pieces[row][col] = None
        del piece

    def add_piece(self, row, col, piece):
        pixmap = self.piece_dict[piece]
        scaled = pixmap.scaled(
            self.width // 8,
            self.height // 8,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        color = "w" if piece.isupper() else "b"
        piece = ChessPiece(scaled, self, row, col, color)
        self.addItem(piece)
        self.pieces[row][col] = piece

    def highlite_last_move(self, new_move):
        if self.last_move is not None:
            start = self.last_move.from_square
            target = self.last_move.to_square
            self.lowlite_squares([start, target])
        start, target = (new_move.from_square, new_move.to_square)
        for sq in [start, target]:
            row, col = 7 - sq // 8, sq % 8
            color = "lightyellow" if (row + col) % 2 == 0 else "gold"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)
        self.last_move = new_move

    def make_move(self, move):
        t_row, t_col = 7 - move.to_square // 8, move.to_square % 8
        s_row, s_col = 7 - move.from_square // 8, move.from_square % 8
        if (self.pieces[t_row][t_col]) is not None:
            self.del_piece(t_row, t_col)
        self.pieces[t_row][t_col] = self.pieces[s_row][s_col]
        self.pieces[t_row][t_col].set_square(t_row, t_col)
        self.pieces[s_row][s_col] = None
        from_sq = move.from_square
        to_sq = move.to_square
        if self.super_board.is_en_passant(move):
            if to_sq > from_sq:
                self.del_piece(t_row + 1, t_col)
            else:
                self.del_piece(t_row - 1, t_col)
        if move.promotion is not None:
            self.del_piece(t_row, t_col)
            self.add_piece(t_row, t_col, move.ch)
        if self.super_board.is_castling(move):
            if self.super_board.is_kingside_castling(move):
                rook_start = to_sq + 1
                rook_target = to_sq - 1
            else:
                rook_start = to_sq - 2
                rook_target = to_sq + 1
            rs_row, rs_col = 7 - rook_start // 8, rook_start % 8
            rt_row, rt_col = 7 - rook_target // 8, rook_target % 8
            self.pieces[rt_row][rt_col] = self.pieces[rs_row][rs_col]
            self.pieces[rs_row][rs_col] = None
            self.pieces[rt_row][rt_col].set_square(rt_row, rt_col)

        self.super_board.push(move)
        self.highlite_last_move(move)
        self.clear_moves()
        self.moving, self.staying = self.staying, self.moving
        self.run()

    def run(self):
        self.moving.start()

    def ask_engine(self):
        result = self.engine.play(self.super_board, chess.engine.Limit(depth=5))
        self.make_move(result.move)

    def get_pieces(self):
        return self.pieces

    def set_moving(self, worker):
        worker.update.connect(self.make_move)
        self.moving = worker

    def set_staying(self, worker):
        worker.update.connect(self.make_move)
        self.staying = worker


class PromotionDialog(QDialog):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setModal(True)
        self.selected_piece = None

        # Load the piece pixmaps from load_piece_dict()
        piece_dict = load_piece_dict()

        # Determine promotion pieces based on color
        # White uses uppercase, black uses lowercase
        promo_pieces = (
            ["Q", "R", "B", "N"] if color.lower() == "w" else ["q", "r", "b", "n"]
        )

        chess_pieces = {
            "q": chess.QUEEN,
            "r": chess.ROOK,
            "b": chess.BISHOP,
            "n": chess.KNIGHT,
        }

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create a borderless button for each promotion piece
        for p in promo_pieces:
            btn = QPushButton()
            btn.setIcon(QIcon(piece_dict[p]))
            btn.setIconSize(QSize(64, 64))
            btn.setFlat(True)
            ret_piece = chess_pieces[p.lower()]
            btn.clicked.connect(
                lambda _, piece=ret_piece, ch=p: self.choose_piece(piece, ch)
            )
            layout.addWidget(btn)

    def choose_piece(self, piece, ch):
        self.selected_piece = piece
        self.piece_char = ch
        self.accept()


def choose_promotion(color):
    dialog = PromotionDialog(color)
    if dialog.exec_() == QDialog.Accepted:
        return (dialog.selected_piece, dialog.piece_char)
    else:
        return None
