import curses
import time
import traceback


class Screen(object):
    UP = -1
    DOWN = 1

    def __init__(self, report, updatetime):
        self.screen = curses.initscr()
        curses.noecho()
        self.screen.keypad(True)
        self.screen.nodelay(True)
        self.screen.erase()
        self.screen.refresh()
        self.report = report
        self.updatetime = updatetime
        self.start = 0

    def printline(self, lno, line):
        try:
            self.screen.addstr(lno, 0, line.encode())
        except ValueError:
            pass
        except Exception:
            pass

    def run(self):
        while True:
            try:
                self.screen.erase()
                y, x = self.screen.getmaxyx()
                end = self.start + y - 1
                self.screen.resize(y, x)
                t1 = time.time()
                for lno, line in enumerate(self.report(self.start, end)):
                    self.printline(lno, line + "\n")
                runtime = time.time() - t1
                self.screen.refresh()
                if runtime < self.updatetime:
                    time.sleep(self.updatetime - runtime)
                self.printline(lno, "Refresh Time: %.3f seconds" % (time.time() - t1))
                self.screen.refresh()
                ch = self.screen.getch()
                if ch == curses.KEY_UP:
                    self.start = max(self.start - 1, 0)
                elif ch == curses.KEY_DOWN:
                    self.start += 1
            except KeyboardInterrupt:
                break
            except Exception:
                print(traceback.format_exc())
        curses.endwin()
