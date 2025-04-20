import logging
import sys

import chess
import chess.engine
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (QApplication, QDialog, QFrame, QGraphicsView,
                             QPushButton, QVBoxLayout, QWidget)

from coordinator import Coordinator
from gamesetup import GameSetupDialog
from gui import GuiBoard
from player import Engine, Player


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    app = QApplication(sys.argv)
    dlg = GameSetupDialog()
    if dlg.exec_() != QDialog.Accepted:
        sys.exit(0)
    side = dlg.selected_side()
    engine_path = dlg.engine_path()
    tc = dlg.time_control()

    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(engine_path, debug=True)
    gui_board = GuiBoard(800, 800)

    player = Player(board, gui_board)
    engine_worker = Engine(board, engine)  # Player(board, gui_board)
    moving, staying = (
        (player, engine_worker) if side == "white" else (engine_worker, player)
    )
    coordinator = Coordinator(moving, staying, board, gui_board)
    if side == "black":
        gui_board.reverse()

    view = QGraphicsView(gui_board)
    view.setFrameStyle(QFrame.NoFrame)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.SmoothPixmapTransform)
    view.setFixedSize(gui_board.width, gui_board.height)

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    layout.addWidget(view)
    btn = QPushButton("reverse")
    btn.setFixedWidth(100)
    btn.clicked.connect(gui_board.reverse)
    layout.addWidget(btn, alignment=Qt.AlignCenter)

    container.setWindowTitle("Fishing Pond")
    container.show()
    container.adjustSize()

    coordinator.run()
    ret_code = app.exec_()
    engine.quit()
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
