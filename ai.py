import chess
import time

VALUES = [100, 350, 351, 500, 1000, 0]
PIECES = range(1, 7)  # should probably call piece types


def value(piece_type):
    if piece_type:
        return VALUES[piece_type-1]
    else:
        return 0


# end game if each side has fewer than two of either a minor piece or a rook and no queen.
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
    result = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and (piece.piece_type == chess.KNIGHT or piece.piece_type == chess.BISHOP or piece.piece_type == chess.ROOK):
            if piece.color == chess.WHITE:
                result += len(board.attacks(square))
            else:
                result -= len(board.attacks(square))
    return result


def material(board):
    black_material = sum(map(lambda piece: len(board.pieces(
        piece, chess.BLACK))*value(piece), PIECES))
    white_material = sum(map(lambda piece: len(board.pieces(
        piece, chess.WHITE))*value(piece), PIECES))
    return white_material - black_material


# just distance to enemy pawn, so not actually tropism
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


# todo: Better way to implement would be to take and of enemy pawns with squares in front of pawn and check for nonzero
def is_passed(board, pawn, color):
    direction = 1 if color else -1

    left = pawn - 1 + 8 * direction  # first spots that opposing pawn could be
    right = pawn + 1 + 8 * direction
    front = pawn + 8 * direction

    enemy_pawns = board.pieces(chess.PAWN, not color)

    while front < 64 and front > 0:
        if front in enemy_pawns:
            return False
        front += 8*direction

    if pawn % 8 != 0:
        while left < 64 and left > 0:
            if left in enemy_pawns:
                return False
            left += 8*direction

    if pawn % 8 != 7:
        while right < 64 and right > 0:
            if right in enemy_pawns:
                return False
            right += 8*direction

    return True


def passers(board):
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    white_score = 200 * \
        len([pawn for pawn in white_pawns if is_passed(board, pawn, chess.WHITE)])
    black_score = 200 * \
        len([pawn for pawn in black_pawns if is_passed(board, pawn, chess.BLACK)])

    return white_score - black_score


def eval_early(board):
    if board.result() == '1-0':
        return 10000
    elif board.result() == '0-1':
        return -10000
    elif board.result() == '1/2-1/2':
        return 0

    return mobility(board) + material(board)


def eval_end(board):
    if board.result() == '1-0':
        return 10000
    elif board.result() == '0-1':
        return -10000
    elif board.result() == '1/2-1/2':
        return 0

    return tropism(board) + material(board) + passers(board)


def eval(board):
    if end_game(board):
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


if __name__ == "__main__":
    main()
