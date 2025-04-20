class Coordinator:
    def __init__(self, moving, staying, board, gui):
        self.moving = moving
        self.staying = staying
        self.board = board
        self.gui = gui

    def make_move(self, mv):
        self.board.push(mv)
        self.gui.make_move(mv)
