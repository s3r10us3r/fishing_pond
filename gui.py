import math

import chess
from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QFrame,
                             QGraphicsPixmapItem, QGraphicsRectItem,
                             QGraphicsScene, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QVBoxLayout, QWidget,
                             qApp)


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
    def __init__(self, pixmap, board, row, col, color, reverse=False):
        super().__init__(pixmap, None)
        self.is_reversed = reverse
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
        row, col = self.get_row_col(new_pos)
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

    def get_row_col(self, pos):
        col = normalize_position(pos.x(), self.board.square_width)
        row = normalize_position(pos.y(), self.board.square_height)
        if self.is_reversed:
            return (7 - row, 7 - col)
        return (row, col)

    def clear_moves(self):
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, False)
        self.moves = []

    def set_callback(self, fn):
        self.callback = fn

    def set_square(self, row, col):
        w = self.board.square_width
        h = self.board.square_height
        if self.is_reversed:
            self.setPos((7 - col) * w, (7 - row) * h)
        else:
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

    def refresh_pos(self):
        self.set_square(self.curr_pos[0], self.curr_pos[1])


def normalize_position(pos, div):
    pos = round(pos, -2) // div
    pos = max(min(pos, 7), 0)
    return int(pos)


class GuiBoard(QGraphicsScene):
    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height
        self.square_height = height // 8
        self.square_width = width // 8
        self.pieces = [[None for _ in range(8)] for _ in range(8)]
        self.is_reversed = False

        self.piece_dict = load_piece_dict()
        self._render_squares()
        self.last_move = None

    def reverse(self):
        self.is_reversed = not self.is_reversed
        for row in self.pieces:
            for piece in row:
                if piece is not None:
                    piece.is_reversed = self.is_reversed
                    piece.refresh_pos()
        self.lowlite_squares(list(range(64)))
        if self.last_move is not None:
            self.highlite_last_move(self.last_move)

    def end_game(self, reason):
        self._clear_pieces()
        QMessageBox.information(None, "Game Over", reason)
        qApp.quit()

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
        self._clear_pieces()
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
                piece = ChessPiece(scaled, self, row, col, color, self.is_reversed)
                self.addItem(piece)
                self.pieces[row][col] = piece

    def _clear_pieces(self):
        for row in self.pieces:
            for piece in row:
                if piece is not None:
                    self.removeItem(piece)
        self.pieces = [[None for _ in range(8)] for _ in range(8)]

    def highlite_squares(self, squares):
        for sq in squares:
            (row, col) = self.sq_to_row_col(sq)
            color = "pink" if (row + col) % 2 == 0 else "red"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)

    def lowlite_squares(self, squares):
        for sq in squares:
            (row, col) = self.sq_to_row_col(sq)
            color = "white" if (row + col) % 2 == 0 else "#61262a"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)

    def highlite_last_move(self, new_move):
        if self.last_move is not None:
            start = self.last_move.from_square
            target = self.last_move.to_square
            self.lowlite_squares([start, target])
        start, target = (new_move.from_square, new_move.to_square)
        for sq in [start, target]:
            row, col = self.sq_to_row_col(sq)
            color = "lightyellow" if (row + col) % 2 == 0 else "gold"
            brush = QBrush(QColor(color))
            self.squares[row][col].setBrush(brush)
        self.last_move = new_move

    def sq_to_row_col(self, sq):
        if self.is_reversed:
            sq = 63 - sq
        return (7 - sq // 8, sq % 8)

    def get_pieces(self):
        return self.pieces


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
