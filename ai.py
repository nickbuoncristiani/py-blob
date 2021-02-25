import chess
import chess.engine
import time
import asyncio

VALUES = [100, 350, 351, 500, 1000, 0]
PIECES = range(1, 7)
MINOR_ROOK = range(2, 5)  # minor piece or rook


def value(piece_type):
    if piece_type:
        return VALUES[piece_type-1]
    else:
        return 0


def in_range(square):
    return square >= 0 and square < 64


def end_game(board):

    if len(board.pieces(chess.QUEEN, chess.BLACK) | board.pieces(chess.QUEEN, chess.WHITE)) != 0:
        return False
    elif len(board.pieces(chess.ROOK, chess.BLACK) | board.pieces(chess.KNIGHT, chess.BLACK) | board.pieces(chess.BISHOP, chess.BLACK)) > 2:
        return False
    elif len(board.pieces(chess.ROOK, chess.WHITE) | board.pieces(chess.KNIGHT, chess.WHITE) | board.pieces(chess.BISHOP, chess.WHITE)) > 2:
        return False
    else:
        return True


def mobility(board):
    side_to_move = board.turn

    board.turn = chess.WHITE
    white_score = len([move for move in board.legal_moves if board.piece_type_at(
        move.from_square) in MINOR_ROOK])

    board.turn = chess.BLACK
    black_score = len([move for move in board.legal_moves if board.piece_type_at(
        move.from_square) in MINOR_ROOK])

    board.turn = side_to_move
    return white_score - black_score


def material(board):
    black_material = sum(map(lambda piece: len(board.pieces(
        piece, chess.BLACK))*value(piece), PIECES))
    white_material = sum(map(lambda piece: len(board.pieces(
        piece, chess.WHITE))*value(piece), PIECES))
    return white_material - black_material


def tropism(board):
    w_king = board.king(chess.WHITE)
    b_king = board.king(chess.BLACK)
    w_score, b_score = 0, 0

    if len(board.pieces(chess.PAWN, chess.BLACK)) > 0:
        w_score = min(chess.square_distance(w_king, pawn)
                      for pawn in board.pieces(chess.PAWN, chess.BLACK))

    if len(board.pieces(chess.PAWN, chess.WHITE)) > 0:
        b_score = min(chess.square_distance(b_king, pawn)
                      for pawn in board.pieces(chess.PAWN, chess.WHITE))

    return -(w_score - b_score)  # negate because closer is better


def is_passed(board, pawn, color):
    enemy_pawns = board.pieces(chess.PAWN, not color)
    opposing_squares = squares_ahead(pawn, color)
    if chess.square_file(pawn) != 0:
        opposing_squares |= squares_ahead(pawn-1, color)
    if chess.square_file(pawn) != 7:
        opposing_squares |= squares_ahead(pawn+1, color)
    return len(enemy_pawns & opposing_squares) == 0


# get square set of squares in front of pawn on same file
def squares_ahead(pawn, color):
    direction = -1 if color == chess.BLACK else 1
    return chess.SquareSet(pawn + step*8*direction for step in range(1, 8) if in_range(pawn + step*8*direction))


def passers(board):
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    white_score = 200 * \
        len([pawn for pawn in white_pawns if is_passed(board, pawn, chess.WHITE)])
    black_score = 200 * \
        len([pawn for pawn in black_pawns if is_passed(board, pawn, chess.BLACK)])

    return white_score - black_score


def eval_early(board):
    return mobility(board) + material(board)


def eval_end(board):
    return tropism(board) + material(board) + passers(board)


def eval(board):
    if board.result() == '1-0':
        return 10000
    elif board.result() == '0-1':
        return -10000
    elif board.result() == '1/2-1/2':
        return 0
    elif end_game(board):
        return eval_end(board)
    else:
        return eval_early(board)


def flipped_eval(board):
    if board.turn == chess.WHITE:
        return eval(board)
    else:
        return -eval(board)


def iterative_deepening(board, start, thinking_time=2):
    depth = 0
    moves = []
    while time.time() - start < thinking_time:
        moves = root_move(board, depth, moves)
        depth += 1
    return moves[0]


# get list of possible moves sorted best to worst.
def root_move(board, depth, prev_moves=[]):
    alpha = -10000
    beta = 10000

    if len(prev_moves) == 0:  # then sort heuristically
        moves = list(board.legal_moves)
        moves.sort(key=lambda move: move_order_key(move, board))
    else:
        moves = prev_moves

    out_moves = []

    for move in moves:
        board.push(move)
        score = -ab_search(board, depth, -beta, -alpha)
        board.pop()

        if score > alpha:
            alpha = score

        out_moves.append((move, score))

    out_moves.sort(key=lambda pair: -pair[1])
    out_moves = [move for move, _ in out_moves]

    return out_moves


def ab_search(board, depth, alpha, beta):

    if depth <= 0:
        score = quiesce(board, alpha, beta)
        if score > beta:
            return beta
        elif score < alpha:
            return alpha
        else:
            return score

    moves = list(board.legal_moves)
    moves.sort(key=lambda move: move_order_key(move, board))

    for move in moves:
        board.push(move)

        subdepth = depth - 1
        if board.is_check():
            subdepth = depth

        score = -ab_search(board, subdepth, -beta, -alpha)

        board.pop()

        if score >= beta:
            return beta
        elif score > alpha:
            alpha = score

    return alpha


def quiesce(board, alpha, beta):

    baseline = flipped_eval(board)
    if board.is_game_over():
        return baseline

    if baseline >= beta and not board.is_check():
        return beta
    elif baseline > alpha and not board.is_check():
        alpha = baseline

    if board.is_check():
        moves = list(board.legal_moves)
    else:
        moves = list(filter(lambda move: quiesce_condition(
            move, board), board.legal_moves))  # take only moves which satisfy quiesce condition

    moves.sort(key=lambda move: move_order_key(move, board))

    for move in moves:
        board.push(move)
        score = -quiesce(board, -beta, -alpha)
        board.pop()
        if score >= beta:
            return beta
        elif score > alpha:
            alpha = score

    return alpha


def quiesce_condition(move, board):
    if board.is_capture(move) or move.promotion == chess.QUEEN:
        return True
    else:
        return False


def move_order_key(move, board):
    if board.is_capture(move):
        return -value(board.piece_type_at(move.to_square))
    elif move.promotion == chess.QUEEN:
        return -value(chess.QUEEN)
    elif board.gives_check(move):
        return -50
    else:
        return 0


def main():
    board = chess.Board()

    engine = chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\nbuon\Desktop\stockfish_2\stockfish")

    while not board.is_game_over():
        print(board)
        result = engine.play(board, chess.engine.Limit(time=0.1))
        board.push(result.move)

    engine.quit()

    """
    while not board.is_game_over():
        print(board)
        while True:
            try:
                moveSan = input("your move: ")
                move = board.parse_san(moveSan)
            except ValueError:
                print('move is illegal or ambigious. please try again')
                continue
            board.push(move)
            print(board)
            print('computer thinking')
            board.push(iterative_deepening(board, time.time()))
            break
    """


if __name__ == "__main__":
    main()
