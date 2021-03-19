import chess
import chess.engine
import chess.pgn
import time
import random

VALUES = [100, 350, 351, 500, 1000, 0]
PIECES = range(1, 7)
MINOR_ROOK = range(2, 5)  # minor piece or rook
CENTER = chess.SquareSet([27, 28, 35, 36])
WHITE_SIDE = chess.SquareSet(range(0, 32))
BLACK_SIDE = chess.SquareSet(range(32, 64))

safe_cols = chess.BB_FILE_A | chess.BB_FILE_B | chess.BB_FILE_C | chess.BB_FILE_F | chess.BB_FILE_G | chess.BB_FILE_H


class Board:
    def __init__(self, board=chess.Board()):
        self.board = board

        self.mat = material(board)
        self.mat_stack = []

        self.non_ray_space = 0
        self.non_ray_stack = []

    def reset(self):
        self.board.reset()
        self.mat = 0
        self.mat_stack = []

        self.non_ray_space = 0
        self.non_ray_stack = []

    def push(self, move):
        mult = 1 if self.board.turn == chess.WHITE else -1
        if move.promotion:  # bug if we promote to knight
            mat_diff = mult * \
                (value(move.promotion) - value(chess.PAWN))
            self.mat += mat_diff
            self.mat_stack.append(mat_diff)
            self.non_ray_stack.append(0)
            self.board.push(move)
            return

        side = WHITE_SIDE if self.board.turn == chess.WHITE else BLACK_SIDE
        enemy_side = WHITE_SIDE if self.board.turn == chess.BLACK else BLACK_SIDE

        mat_diff = mult * value(self.board.piece_type_at(move.to_square))
        self.mat += mat_diff
        self.mat_stack.append(mat_diff)

        non_ray_diff = 0

        if self.board.piece_type_at(move.to_square) and self.board.piece_type_at(move.to_square) <= chess.KNIGHT:
            non_ray_diff += mult * 3 * \
                len(self.board.attacks(move.to_square) &
                    side)  # reduce the non-ray space of opposing side

        if self.board.piece_type_at(move.from_square) and self.board.piece_type_at(move.from_square) <= chess.KNIGHT:
            non_ray_diff -= mult * 3 * \
                len(self.board.attacks(move.from_square) &
                    enemy_side)  # reduce the non-ray space of friendly side

        self.board.push(move)

        if self.board.piece_type_at(move.to_square) and self.board.piece_type_at(move.to_square) <= chess.KNIGHT:
            non_ray_diff += mult * 3 * \
                len(self.board.attacks(move.to_square) &
                    enemy_side)  # increase non-ray space of friendly side

        self.non_ray_space += non_ray_diff
        self.non_ray_stack.append(non_ray_diff)

    def pop(self):
        self.mat -= self.mat_stack.pop()
        self.non_ray_space -= self.non_ray_stack.pop()
        self.board.pop()

    def space(self):
        return self.non_ray_space + self.ray_space()

    def center_control(self):
        result = 0
        for square in CENTER:
            result += len(self.board.attackers(chess.WHITE, square)) - \
                len(self.board.attackers(chess.BLACK, square))
        return 2 * result

    def king_safety(self):
        w_king = self.board.king(chess.WHITE)
        b_king = self.board.king(chess.BLACK)
        w_score, b_score = 0, 0

        safe_wpawns = self.board.pieces(chess.PAWN, chess.WHITE) & safe_cols
        safe_bpawns = self.board.pieces(chess.PAWN, chess.BLACK) & safe_cols

        if len(safe_wpawns) > 0:
            distances = [chess.square_distance(w_king, pawn)
                         for pawn in safe_wpawns]
            distances.sort()
            w_score = sum(distances[:3])

        if len(safe_bpawns) > 0:
            distances = [chess.square_distance(b_king, pawn)
                         for pawn in safe_bpawns]
            distances.sort()
            b_score = sum(distances[:3])

        return 20 * -(w_score - b_score)

    # Queen space is valued 1/3 of other pieces.
    def ray_space(self):
        ray_space = 0
        ray_space += 3 * sum(len(self.board.attacks(square) & BLACK_SIDE)
                             for square in self.board.pieces(chess.ROOK, chess.WHITE) | self.board.pieces(chess.BISHOP, chess.WHITE))

        ray_space += sum(len(self.board.attacks(square) & BLACK_SIDE)
                         for square in self.board.pieces(chess.QUEEN, chess.WHITE))

        ray_space -= 3 * sum(len(self.board.attacks(square) & WHITE_SIDE)
                             for square in self.board.pieces(chess.ROOK, chess.BLACK) | self.board.pieces(chess.BISHOP, chess.BLACK))

        ray_space -= sum(len(self.board.attacks(square) & WHITE_SIDE)
                         for square in self.board.pieces(chess.QUEEN, chess.BLACK))
        return ray_space

    def eval(self):
        if self.board.result() == '1-0':
            return 10000
        elif self.board.result() == '0-1':
            return -10000
        elif self.board.result() == '1/2-1/2':
            return 0
        if end_game(self.board):
            return eval_end(self.board)
        else:
            return self.mat + self.space() + self.center_control()  # + self.king_safety()

    def flipped_eval(self):
        if self.board.turn == chess.WHITE:
            return self.eval()
        else:
            return -self.eval()

    def set_fen(self, fen):
        return


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


def king_activity(board):
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
    return king_activity(board) + material(board) + passers(board)


def eval(board):
    return 0
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


# get list of possible moves sorted best to worst.
def root_move(board, depth, prev_best_move, prev_moves, thinking, nodes):
    alpha = -10000
    beta = 10000
    nodes[0] += 1

    if len(prev_moves) != 0:
        moves = list(filter(lambda move: move[0] !=
                            prev_best_move, prev_moves))
        moves.sort(key=lambda movescore: -movescore[1])
        moves = list(map(lambda movescore: movescore[0], moves))
    else:
        moves = list(filter(lambda move: move !=
                            prev_best_move, board.board.legal_moves))
        moves.sort(key=lambda move: move_order_key(move, board))
    moves = list(filter(lambda move: move !=
                        prev_best_move, board.board.legal_moves))
    moves.sort(key=lambda move: move_order_key(move, board))
    if prev_best_move:
        moves.insert(0, prev_best_move)
    set_zero = False

    best_move = moves[0]
    prev_moves.clear()
    for move in moves:
        board.push(move)
        #score = -ab_search(board, depth, -beta, -alpha, thinking)
        if set_zero:
            score = -ab_search(board, depth, -
                               (alpha+1), -alpha, thinking, nodes, zero=True)
            if score > alpha:
                score = -ab_search(board, depth, -beta, -
                                   alpha, thinking, nodes)
        else:
            score = -ab_search(board, depth, -beta, -alpha, thinking, nodes)
            set_zero = True
        board.pop()

        if score > alpha:
            alpha = score
            best_move = move

        if not thinking[0]:
            return prev_best_move

        prev_moves.append((move, score))

    # print(prev_moves)
    # print()
    return best_move


def ab_search(board, depth, alpha, beta, thinking, nodes, zero=False):
    nodes[0] += 1
    if depth <= 0 or board.board.is_game_over():
        return quiesce(board, alpha, beta, thinking, nodes)

    moves = list(board.board.legal_moves)
    moves.sort(key=lambda move: quiesce_order_key(move, board))
    set_zero = False

    score = -10000
    for move in moves:
        board.push(move)

        subdepth = depth - 1
        if board.board.is_check():
            subdepth = depth

        # score = max(score, -ab_search(board, subdepth,
        #                              -beta, -alpha, thinking, zero=True))

        if zero:
            score = max(score, -ab_search(board, subdepth,
                                          -beta, -alpha, thinking, nodes, zero=True))
        elif set_zero:
            test_score = -ab_search(board, subdepth, -
                                    (alpha+1), -alpha, thinking, nodes, zero=True)
            if test_score > alpha:
                score = max(score, -ab_search(board,
                                              subdepth, -beta, -alpha, thinking, nodes))
        else:
            score = max(score, -ab_search(board,
                                          subdepth, -beta, -alpha, thinking, nodes))
            set_zero = True

        board.pop()

        if score >= beta:
            return score
        elif score > alpha:
            alpha = score
        if not thinking[0]:
            return score

    return score


def quiesce(board, alpha, beta, thinking, nodes):
    nodes[0] += 1
    baseline = board.flipped_eval()
    if board.board.is_game_over():
        return baseline

    if baseline >= beta and not board.board.is_check():
        return baseline
    elif baseline > alpha and not board.board.is_check():
        alpha = baseline

    if board.board.is_check():
        moves = list(board.board.legal_moves)
    else:
        moves = list(filter(lambda move: quiesce_condition(
            move, board), board.board.legal_moves))  # take only moves which satisfy quiesce condition

    moves.sort(key=lambda move: quiesce_order_key(move, board))

    score = baseline
    for move in moves:
        board.push(move)
        score = max(score, -quiesce(board, -beta, -alpha, thinking, nodes))
        board.pop()
        if score >= beta:
            return score
        elif score > alpha:
            alpha = score
        if not thinking[0]:
            return score

    return score


def quiesce_condition(move, board):
    if board.board.is_capture(move) or move.promotion == chess.QUEEN:
        return True
    else:
        return False


def quiesce_order_key(move, board):
    if board.board.is_capture(move):
        return -value(board.board.piece_type_at(move.to_square))
    elif move.promotion == chess.QUEEN:
        return -value(chess.QUEEN)
    elif board.board.gives_check(move):
        return -150
    else:
        return 0


def move_order_key(move, board):
    board.push(move)
    score = -quiesce(board, -10000, 10000, [True], [0])
    board.pop()
    return -score


def eval_order_key(move, board):
    board.push(move)
    score = -board.flipped_eval()
    board.pop()
    return -score


if __name__ == "__main__":
    board = Board()
    # board.set_fen(
    #    'rnb1kbnr/ppq2ppp/2p5/3pp3/8/P1NPBN1P/1PP1PPP1/R2QKB1R w KQkq - 0 7')
    board.push(chess.Move.from_uci('d2d4'))
    board.push(chess.Move.from_uci('d7d5'))
    board.push(chess.Move.from_uci('b1d2'))
    board.push(chess.Move.from_uci('c8f5'))
    board.push(chess.Move.from_uci('g1f3'))
    board.push(chess.Move.from_uci('e7e6'))
    board.push(chess.Move.from_uci('c2c4'))
    board.push(chess.Move.from_uci('b8c6'))
    board.push(chess.Move.from_uci('c4d5'))
    board.push(chess.Move.from_uci('d8d5'))
    board.push(chess.Move.from_uci('a2a3'))
    print(board)
    start = time.time()
    moves = []
    best_move = None
    best_move = root_move(board, 0, best_move, moves, [True])
    best_move = root_move(board, 1, best_move, moves, [True])
    best_move = root_move(board, 2, best_move, moves, [True])
    #best_move = root_move(board, 3, best_move, moves, [True])
    #best_move = root_move(board, 4, best_move, moves, [True])
    #best_move = root_move(board, 5, best_move, moves, [True])
    print(best_move)
    print(time.time() - start)
