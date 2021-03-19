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


def test_king_activity():
    board = chess.Board()
    board.set_fen('2k2b2/p3pp1q/3p3p/8/3PP3/3P4/5P2/3K2N1 w - - 0 1')
    assert ai.king_activity(board) == -1


def test_mobility():
    board = chess.Board()
    board.set_fen('b6k/8/8/8/8/8/7B/K7 w - - 0 1')
    assert ai.mobility(board) == 0, ai.mobility(board)
    board.set_fen('b6k/8/8/4n3/8/8/7B/K7 w - - 0 1')
    assert ai.mobility(board) == -11, ai.mobility(board)
    board.set_fen('b6k/8/8/4n3/8/8/7B/KR6 w - - 0 1')
    assert ai.mobility(board) == 2, ai.mobility(board)


def test_kingsafety():
    board = ai.Board()
    assert board.king_safety() == 0, board.king_safety()
    board.push(chess.Move.from_uci('f2f4'))
    assert board.king_safety() == -40, board.king_safety()
    board.push(chess.Move.from_uci('f7f5'))
    assert board.king_safety() == 0, board.king_safety()
    board.push(chess.Move.from_uci('g1f3'))
    board.push(chess.Move.from_uci('g8f6'))
    board.push(chess.Move.from_uci('e2e4'))
    board.push(chess.Move.from_uci('e7e5'))
    board.push(chess.Move.from_uci('f1b5'))
    board.push(chess.Move.from_uci('f8b4'))
    assert board.king_safety() == 0, board.king_safety()
    board.push(chess.Move.from_uci('e1g1'))
    assert board.king_safety() == 40, board.king_safety()
    board.push(chess.Move.from_uci('e8g8'))
    assert board.king_safety() == 0, board.king_safety()


def test_push():
    board = ai.Board()
    board.push(chess.Move.from_uci('e2e3'))
    assert board.space() == 7, board.space()

    board.pop()
    assert board.space() == 0, board.space()

    board.push(chess.Move.from_uci('g1f3'))
    assert board.space() == 6, board.space()

    board.pop()
    assert board.space() == 0, board.space()

    # Big game
    board.push(chess.Move.from_uci('e2e4'))
    assert board.space() == 13, board.space()
    board.push(chess.Move.from_uci('e7e5'))
    assert board.space() == 0, board.space()
    board.push(chess.Move.from_uci('g1f3'))
    assert board.space() == 5, board.space()
    board.push(chess.Move.from_uci('g8f6'))
    assert board.space() == 0, board.space()
    board.push(chess.Move.from_uci('f3e5'))
    assert board.space() == 13, board.space()
    assert board.mat == 100, board.mat
    #assert board.eval() == 110, board.eval()
    board.push(chess.Move.from_uci('f8c5'))
    assert board.space() == 4, board.space()
    assert board.mat == 100, board.mat
    #assert board.eval() == 101, board.eval()

    board.pop()
    assert board.space() == 13, board.space()
    assert board.mat == 100, board.mat
    #assert board.eval() == 110, board.eval()
    board.pop()
    assert board.space() == 0, board.space()
    assert board.mat == 0, board.mat
    #assert board.eval() == 0, board.eval()
    board.pop()
    assert board.space() == 5, board.space()
    board.pop()
    assert board.space() == 0, board.space()
    board.pop()
    assert board.space() == 13, board.space()
    board.pop()
    assert board.space() == 0, board.space()


def main():
    # test_end_game()
    # test_mobility()
    # test_passers()
    # test_king_activity()
    test_push()
    test_kingsafety()
    print('good')


if __name__ == "__main__":
    main()
