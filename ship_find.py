import argparse
import itertools
import sys

from optilog.modelling import *
from optilog.formulas import CNF
from optilog.solvers.sat import Cadical152

from utils import (
    read_ship_find,
    cell,
    ship,
    visualize,
    visualize_raw,
    get_grid_from_model,
)


def encode(sf):
    cnf = CNF()

    nrows = len(sf.rows)
    ncolumns = len(sf.columns)

    # Fixed
    for i, j in sf.fixed_cells:
        if sf.fixed_cells[(i, j)] == 1:
            # YOUR CODE HERE
            cnf.add_clause([cell(i, j)])
        else:
            # YOUR CODE HERE
            cnf.add_clause([~cell(i,j)])

    # Ships must be placed somewhere
    for ship_index, ship_size in enumerate(sf.ships):
        lits = []
        for init_row in range(nrows):
            for init_column in range(ncolumns):
                for ship_dir in ["E", "S"]:
                    lits.append(ship(init_row, init_column, ship_index, ship_dir))
        # YOUR CODE HERE
        cnf.add_clauses(at_least_one(lits))

    # Ships can not have same starting position
    # YOUR CODE HERE 
    for init_row in range(nrows):
        for init_column in range(ncolumns):
            # Collect all possible literals for ships starting in this position
            lits = []
            for ship_index, ship_size in enumerate(sf.ships):
                for ship_dir in ["E", "S"]:
                    lits.append(ship(init_row, init_column, ship_index, ship_dir))
            # Add a pairwise "at most one" constraint
            cnf.add_clauses(at_most_one(lits))

    # Ship constraints
    for ship_index, ship_size in enumerate(sf.ships):
        for init_row in range(nrows):
            for init_column in range(ncolumns):
                for ship_dir in ["E", "S"]:

                    if ship_dir == "S":
                        # dissallowed starting positions
                        if nrows - init_row < ship_size or sf.columns[init_column] < ship_size:
                            # YOUR CODE HERE
                            cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir)])
                            continue

                        # ship and water cells
                        for col in range(init_column - 1, init_column + 2):
                            for row in range(init_row - 1, init_row + ship_size + 1):
                                if row < 0 or row > nrows - 1 or col < 0 or col > ncolumns - 1:
                                    # out of range
                                    continue
                                if row >= init_row and row < (init_row + ship_size) and col == init_column:
                                    # ship
                                    cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir), cell(row, col)])
                                    
                                else:
                                    # water
                                    cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir), ~cell(row, col)])

                    else:
                        # ship_dir is 'E'

                         # submarine only have direction S
                        if ship_size == 1:
                            # YOUR CODE HERE
                            cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir)])    
                            continue

                        # dissallowed starting positions
                        if ncolumns - init_column < ship_size or sf.rows[init_row] < ship_size:
                            cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir)])
                            continue

                        # ship and water cells
                        for row in range(init_row - 1, init_row + 2):
                            for col in range(init_column - 1, init_column + ship_size + 1):
                                if row < 0 or row > nrows - 1 or col < 0 or col > ncolumns - 1:
                                    # out of range
                                    continue
                                if col >= init_column and col < (init_column + ship_size) and row == init_row:
                                    # ship
                                    """ YOUR CODE HERE"""
                                    cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir), cell(row, col)])
                                else:
                                    # water
                                    """ YOUR CODE HERE"""
                                    cnf.add_clause([~ship(init_row, init_column, ship_index, ship_dir), ~cell(row, col)])
    
    # Row constraints
    for row_index, n_parts in enumerate(sf.rows):
        if n_parts == 0:
            for column_index in range(ncolumns):
                # YOUR CODE HERE
                cnf.add_clause([~cell(row_index, column_index)])
        else:
            lits = []
            for comb in itertools.combinations(range(ncolumns), n_parts):
                cube = [cell(row_index, column_index) for column_index in comb]
                aux_var = reify_cube(cube, cnf)
                lits.append(aux_var)
            
            # YOUR CODE HERE
            cnf.add_clauses(exactly_one(lits))

    # Column constraints
    # YOUR CODE HERE
    for column_index, n_parts in enumerate(sf.columns):
        if n_parts == 0:
            for row_index in range(nrows):
                cnf.add_clause([~cell(row_index, column_index)])
        else:
            lits = []
            for comb in itertools.combinations(range(nrows), n_parts):
                cube = [cell(row_index, column_index) for row_index in comb]
                aux_var = reify_cube(cube, cnf)
                lits.append(aux_var)

            cnf.add_clauses(exactly_one(lits))
 
    return cnf


def reify_cube(cube, cnf):
    aux_var = Bool("aux_{:d}".format(cnf.max_var() + 1))

    cnf.add_clause([aux_var] + [~lit for lit in cube])
    for lit in cube:
        cnf.add_clause([~aux_var, lit])

    return aux_var


def reify_clause(clause, cnf):
    aux_var = Bool("aux_{:d}".format(cnf.max_var() + 1))

    cnf.add_clause([~aux_var] + [lit for lit in clause])
    for lit in clause:
        cnf.add_clause([aux_var, ~lit])

    return aux_var


def at_most_one(lits):
    clauses = []
    for i in range(len(lits) - 1):
        for j in range(i + 1, len(lits)):
            v1 = lits[i]
            v2 = lits[j]
            clauses.append([~v1, ~v2])
    return clauses


def at_least_one(lits):
    clauses = [[x for x in lits]]
    return clauses


def exactly_one(lits):
    return at_least_one(lits) + at_most_one(lits)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--visualization", type=str, choices=["raw", "rich", "quiet"], default="rich"
    )
    return parser.parse_args()


def main(args):
    sf = read_ship_find(args.input_file)

    cnf = encode(sf)

    s = Cadical152()
    s.add_clauses(cnf.clauses)
    has_solution = s.solve()
    print("Has solution?", has_solution)

    if has_solution:
        model = s.model()
        model = cnf.decode_dimacs([lit for lit in model if lit > 0])
        n_rows, n_columns = len(sf.rows), len(sf.columns)
        grid = get_grid_from_model(n_rows, n_columns, model)
        if args.visualization == "rich":
            visualize(grid)
        elif args.visualization == "raw":
            visualize_raw(grid)
        print()
        if args.verify:
            from checker import WrongSolutionError, check_solution
            try:
                print("VERIFICATION")
                print("------------")
                check_solution(sf, model)
                print()
            except WrongSolutionError as e:
                print("ERROR")
                print(e)
                sys.exit(-1)


if __name__ == "__main__":
    args = parse_args()
    main(args)
