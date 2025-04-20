import logging
import sys

import chess
import chess.engine
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QGraphicsView

from gui import GuiBoard
from player import Engine, Player


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    app = QApplication(sys.argv)

    board = chess.Board()
    engine_path = "/home/tradeckm/projekt_dyplomowy/barbel/target/release/barbel"
    engine = chess.engine.SimpleEngine.popen_uci(engine_path, debug=True)
    gui_board = GuiBoard(800, 800, board, engine)

    pieces = gui_board.get_pieces()
    player = Player(pieces, board)
    engine_worker = Engine(board, engine)
    gui_board.set_moving(player)
    gui_board.set_staying(engine_worker)

    view = QGraphicsView(gui_board)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.SmoothPixmapTransform)

    view.setFixedSize(1000, 1000)
    view.setWindowTitle("Fishing Pond")

    view.show()
    gui_board.run()
    ret_code = app.exec_()
    engine.quit()
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
