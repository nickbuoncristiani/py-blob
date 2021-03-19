import threading
import ai
import time
import chess


class Interface:
    def __init__(self):
        self.thinking = [False]
        self.stop_timer = True
        self.search_thread = None
        self.wait_thread = None
        self.board = ai.Board()

    def think(self):
        best_move = None
        move_list = []
        depth = 0
        nodes = [0]
        start = time.time()
        while self.thinking[0]:
            print(nodes[0])
            best_move = ai.root_move(
                self.board, depth, best_move, move_list, self.thinking, nodes)
            depth += 1
        self.stop_timer = True

        print('bestmove ' + best_move.uci(), flush=True)
        print('nodes/sec ' + str(nodes[0]/(time.time()-start)), flush=True)

    def wait(self, wait_time):
        start_time = time.time()
        while time.time() - start_time < wait_time/1000:
            if self.stop_timer:
                return

        self.thinking[0] = False

    def setup(self, tokens):
        if tokens[1] == 'fen':
            fen = ''.join([str(token)+' ' for token in tokens[2:]])
            self.board.set_fen(fen)
        elif tokens[1] == 'startpos':
            self.board.reset()
            if len(tokens) > 3 and tokens[2] == 'moves':
                for move in tokens[3:]:
                    self.board.push(chess.Move.from_uci(move))

    def start_thinking(self, wait_time):
        self.thinking[0] = True
        self.search_thread = threading.Thread(target=self.think)
        self.search_thread.start()

        self.stop_timer = False
        self.wait_thread = threading.Thread(
            target=self.wait, args=(wait_time,))
        self.wait_thread.start()

    def stop_thinking(self):
        self.thinking[0] = False
        if self.search_thread:
            self.search_thread.join()

        self.stop_timer = True
        if self.wait_thread:
            self.wait_thread.join()

    def go(self, tokens):
        if 'movetime' in tokens:
            think_time = int(tokens[tokens.index('movetime') + 1])
        elif 'wtime' in tokens and self.board.board.turn == chess.WHITE:
            think_time = int(tokens[tokens.index('wtime') + 1])/20
        elif 'btime' in tokens and self.board.board.turn == chess.BLACK:
            think_time = int(tokens[tokens.index('btime') + 1])/20
        else:
            think_time = 10000000000
        self.start_thinking(think_time)

    def listen(self):
        while True:
            tokens = input().split(' ')
            if tokens[0] == 'uci':
                print('id name py-blob')
                print('id author Nicholas Buoncristiani Jerome Wei')
                print('uciok')
            elif tokens[0] == 'isready':
                print('readyok')
            elif tokens[0] == 'ucinewgame':
                self.stop_thinking()
                self.board.reset()
            elif tokens[0] == 'position':
                self.setup(tokens)
            elif tokens[0] == 'stop':
                self.stop_thinking()
            elif tokens[0] == 'go':
                try:
                    self.go(tokens)
                except Exception as e:
                    print(e)
            elif tokens[0] == 'quit':
                self.stop_thinking()
                return


def main():
    a = Interface()
    a.listen()


if __name__ == "__main__":
    main()
