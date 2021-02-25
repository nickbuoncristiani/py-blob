import chess
import ai

positions = [
    '2k2b2/1p1n4/3p4/8/1P6/3P4/5P2/R2K4 w - - 0 1',
    '2k2b2/1p1n4/3p4/8/1P6/3P4/4BP2/R2K2N1 w - - 0 1',
    '2k2b2/1p1n4/3p4/8/1P4R1/3P4/4NP2/R2K2N1 w - - 0 1',
    '2k2b2/1p2pp1q/3p4/8/1P1PP3/3P4/5P2/3K2N1 w - - 0 1'
]


def test_end_game():
    board = chess.Board()
    board.set_fen('2k2b2/1p1n4/3p4/8/1P6/3P4/5P2/R2K4 w - - 0 1')
    assert(ai.end_game(board) == True)
    board.set_fen('2k2b2/1p1n4/3p4/8/1P6/3P4/4BP2/R2K2N1 w - - 0 1')
    assert(ai.end_game(board) == False)
    board.set_fen('2k2b2/1p1n4/3p4/8/1P4R1/3P4/4NP2/R2K2N1 w - - 0 1')
    assert(ai.end_game(board) == False)
    board.set_fen('2k2b2/1p2pp1q/3p4/8/1P1PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert(ai.end_game(board) == False)


def test_passers():
    board = chess.Board()
    board.set_fen('2k2b2/1p1n4/3p4/8/1P6/3P4/5P2/R2K4 w - - 0 1')
    assert ai.passers(board) == 200, ai.passers(board)
    board.set_fen('2k2b2/1p2pp1q/3p4/8/1P1PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.passers(board) == 0, ai.passers(board)
    board.set_fen('2k2b2/1p2pp1q/3p3p/8/1P1PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.passers(board) == -200, ai.passers(board)
    board.set_fen('2k2b2/p3pp1q/3p3p/8/1P1PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.passers(board) == -200, ai.passers(board)
    board.set_fen('2k2b2/p3pp1q/3p3p/8/3PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.passers(board) == -400, ai.passers(board)


def test_tropism():
    board = chess.Board()
    board.set_fen('2k2b2/p3pp1q/3p3p/8/3PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.tropism(board) == -1


def test_mobility():
    board = chess.Board()
    board.set_fen('b6k/8/8/8/8/8/7B/K7 w - - 0 1')
    assert ai.mobility(board) == 0, ai.mobility(board)
    board.set_fen('b6k/8/8/4n3/8/8/7B/K7 w - - 0 1')
    assert ai.mobility(board) == -11, ai.mobility(board)
    board.set_fen('b6k/8/8/4n3/8/8/7B/KR6 w - - 0 1')
    assert ai.mobility(board) == 2, ai.mobility(board)


def main():
    test_end_game()
    test_mobility()
    test_passers()
    test_tropism()
    print('good')


if __name__ == "__main__":
    main()
