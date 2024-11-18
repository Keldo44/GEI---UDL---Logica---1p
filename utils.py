from dataclasses import dataclass
from optilog.modelling import *
import sys


def cell(i, j):
    return Bool("cell_{:d}_{:d}".format(i, j))


def ship(row_index, column_index, ship_index, ship_dir):
    return Bool(
        "ship_{:d}_{:d}_{:d}_{}".format(row_index, column_index, ship_index, ship_dir)
    )


def visualize_raw(grid, stderr=False):
    n, m = len(grid), len(grid[0])

    file = sys.stderr if stderr else sys.stdout

    print("-" * (4 * m + 1), file=file)
    for i in range(n):
        print("|", end="", file=file)
        for j in range(m):
            if grid[i][j] == 1:
                print(" * ", end="|", file=file)
            else:
                print("   ", end="|", file=file)
        print("", file=file)
        print("-" * (4 * m + 1), file=file)


def visualize(grid, stderr=False):
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text

    raw_grid = [
        [" " if v == 0 else Text("*", style="bold black on white") for v in row]
        for row in grid
    ]

    console = Console(stderr=stderr)
    table = Table(show_header=True, show_lines=True)
    table.add_column(" ")  # Empty column for row indices
    for j in range(len(grid[0])):
        table.add_column(f"{j}", justify="center")
    for row_indx, row in enumerate(raw_grid):
        table.add_row(f"{row_indx}", *row)
    console.print(table)


def get_cells_from_model(model):
    cell_names_iterator = (
        v.name.split("_")[1:]
        for v in model
        if isinstance(v, Bool) and v.name.startswith("cell_")
    )
    return [tuple(map(int, cell_name)) for cell_name in cell_names_iterator]


def get_ships_from_model(model):
    raw_ships = (
        v.name.split("_")[1:]
        for v in model
        if isinstance(v, Bool) and v.name.startswith("ship_")
    )
    return [
        Ship(coord=(int(ship[0]), int(ship[1])), index=int(ship[2]), direction=ship[3])
        for ship in raw_ships
    ]


def coords_to_grid(n: int, m: int, coords: list[tuple[int, int]]) -> list[list[int]]:
    grid = [[0 for _ in range(m)] for _ in range(n)]
    for x, y in coords:
        grid[x][y] = 1
    return grid


def get_grid_from_model(n, m, model):
    return coords_to_grid(n, m, get_cells_from_model(model))


class ShipFind:
    def __init__(self, rows, columns, ships, fixed_cells):

        self.fixed_cells = fixed_cells
        self.rows = rows
        self.columns = columns
        self.ships = ships


@dataclass
class Ship:
    coord: tuple[int, int]
    index: int
    direction: str
    length: int = -1


def read_ship_find(path, print_dim=True):
    fixed_cells = {}
    with open(path, "r") as f:

        rows = None
        columns = None
        ships = []

        for line in f:

            l = line.split()
            if l[0] == "c":
                continue
            if l[0] == "rows":
                rows = [int(item) for item in l[1:]]
            elif l[0] == "columns":
                columns = [int(item) for item in l[1:]]
            elif l[0] == "ships":
                ships = [int(item) for item in l[1:]]
            elif l[0] in ["water", "piece"]:
                row = int(l[1])
                column = int(l[2])
                if l[0] == "piece":
                    fixed_cells[(row, column)] = 1
                else:
                    fixed_cells[(row, column)] = 0
            else:
                print("Wrong .sf format")
                sys.exit(-1)

    return ShipFind(rows, columns, ships, fixed_cells)
