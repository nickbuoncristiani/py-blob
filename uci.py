import threading
import ai
import time
import chess


class Interface:
    def __init__(self):
        self.thinking = False
        self.stop_timer = True
        self.search_thread = None
        self.wait_thread = None
        self.board = chess.Board()

    def think(self):
        moves = []
        depth = 0
        while self.thinking:
            moves = ai.root_move(self.board, depth, moves, [self.thinking])
            depth += 1
        self.stop_timer = True

        print('bestmove ' + moves[0].uci())

    def wait(self, wait_time):
        start_time = time.time()
        while time.time() - start_time < wait_time/1000:
            if self.stop_timer:
                return

        self.thinking = False

    def setup(self, tokens):
        if tokens[1] == 'fen':
            self.board.set_fen(tokens[2])
        elif tokens[1] == 'startpos' and tokens[2] == 'moves':
            for move in tokens[3:]:
                self.board.push(chess.Move.from_uci(move))

    def start_thinking(self, wait_time):
        self.thinking = True
        self.search_thread = threading.Thread(target=self.think)
        self.search_thread.start()
        self.stop_timer = False
        self.wait_thread = threading.Thread(
            target=self.wait, args=(wait_time,))
        self.wait_thread.start()

    def stop_thinking(self):
        self.thinking = False
        if self.search_thread:
            self.search_thread.join()

        self.stop_timer = True
        if self.wait_thread:
            self.wait_thread.join()

    def go(self, tokens):
        if 'movetime' in tokens:
            think_time = int(tokens[tokens.index('movetime') + 1])
        elif 'wtime' in tokens and self.board.turn == chess.WHITE:
            think_time = int(tokens[tokens.index('wtime') + 1])
        elif 'btime' in tokens and self.board.turn == chess.BLACK:
            think_time = int(tokens[tokens.index('btime') + 1])
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
