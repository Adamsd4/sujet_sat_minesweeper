from dataclasses import dataclass
from pathlib import Path

from cnf import CNF, exactly_k


BASE_DIR = Path(__file__).resolve().parent

INLINE_SAMPLES = {
    "tiny": """
        1.
    """,
    "medium": """
        1..
        2..
        1..
    """,
    "block_5x5": """
        11211
        1...1
        2...1
        1...0
        11100
    """,
    "block_6x6": """
        111111
        1....1
        2....2
        1....1
        1....1
        011100
    """,
    "challenge_7x7": """
        1121211
        1.....1
        2.....2
        1.....1
        1.....1
        0.....0
        0011100
    """,
    "double_8x8": """
        11211000
        1...1000
        2...1000
        1...1211
        1111...1
        0002...2
        0001...1
        00011211
    """,
}

FILE_SAMPLES = {
    "expert_16x30": BASE_DIR / "samples" / "expert_16x30.txt",
    "large_30x40": BASE_DIR / "samples" / "large_30x40.txt",
    "huge_60x60": BASE_DIR / "samples" / "huge_60x60.txt",
}

SAMPLES = tuple(sorted([*INLINE_SAMPLES, *FILE_SAMPLES]))


def load_sample(name: str) -> str:
    if name in INLINE_SAMPLES:
        return INLINE_SAMPLES[name]
    return FILE_SAMPLES[name].read_text(encoding="utf-8")


@dataclass(frozen=True)
class Board:
    cells: tuple[tuple[str, ...], ...]

    @property
    def height(self) -> int:
        return len(self.cells)

    @property
    def width(self) -> int:
        return len(self.cells[0])

    def neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        # Standard 8-neighborhood of Minesweeper.
        result = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = row + dr
                nc = col + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    result.append((nr, nc))
        return result

    def unknown_cells(self) -> list[tuple[int, int]]:
        return [
            (row, col)
            for row in range(self.height)
            for col in range(self.width)
            if self.cells[row][col] == "."
        ]


def parse_board(text: str) -> Board:
    # Spaces are ignored so boards remain readable in multiline strings.
    rows = []
    for raw_line in text.splitlines():
        line = raw_line.strip().replace(" ", "")
        if not line:
            continue
        rows.append(tuple(line))

    if not rows:
        raise ValueError("Board is empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Board rows must have the same width")
    return Board(tuple(rows))


def build_minesweeper_cnf(board: Board) -> tuple[CNF, dict[tuple[int, int], int]]:
    cnf = CNF()
    variables: dict[tuple[int, int], int] = {}

    # Each unknown cell becomes one Boolean variable:
    # True = mine, False = safe.
    for cell in board.unknown_cells():
        valid_cell = False
        for (row, col) in board.neighbors(cell[0], cell[1]):
            if board.cells[row][col] != ".":  # Si tous les voisins d'une case sont inconnus la case sera forcément non forcée, on ne l'ajoute donc pas dans les variables
                valid_cell = True
                break
        if valid_cell:
            variables[cell] = cnf.new_var()

    for row in range(board.height):
        for col in range(board.width):
            clue = board.cells[row][col]
            if not clue.isdigit():
                continue
            # A clue "k" means exactly k neighboring unknown cells are mines.
            unknown_neighbors = [variables[pos] for pos in board.neighbors(row, col) if pos in variables]
            cnf.extend(exactly_k(unknown_neighbors, int(clue)))

    return cnf, variables


def render_board(board: Board, marks: dict[tuple[int, int], str] | None = None) -> str:
    # Optional marks are used to display inferred mines/safe cells.
    marks = marks or {}
    lines = []
    for row in range(board.height):
        chars = []
        for col in range(board.width):
            chars.append(marks.get((row, col), board.cells[row][col]))
        lines.append("".join(chars))
    return "\n".join(lines)
