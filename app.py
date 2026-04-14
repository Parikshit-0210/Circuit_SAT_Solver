from flask import Flask, render_template, jsonify
from pysat.formula import CNF
from pysat.solvers import Solver

app = Flask(__name__)

def solve_with_sat():
    vars_map = {}
    counter = 1

    def new_var(name):
        nonlocal counter
        vars_map[name] = counter
        counter += 1
        return vars_map[name]

    for v in ["A","B","C","D","E","F","G","H","I","J",
              "X1","X2","X3","X4","X5","X6","X7","X8","X9","X10","X11",
              "Z_orig","Z_ext"]:
        new_var(v)

    cnf = CNF()

    # Gate Encodings

    def AND(x, a, b):
        cnf.append([-a, -b, x])
        cnf.append([a, -x])
        cnf.append([b, -x])

    def OR(x, a, b):
        cnf.append([a, b, -x])
        cnf.append([-a, x])
        cnf.append([-b, x])

    def NOT(x, a):
        cnf.append([-a, -x])
        cnf.append([a, x])

    def NAND(x, a, b):
        temp = new_var(f"temp_and_{x}")
        AND(temp, a, b)
        NOT(x, temp)

    def NOR(x, a, b):
        temp = new_var(f"temp_or_{x}")
        OR(temp, a, b)
        NOT(x, temp)

    # Build Circuit

    AND(vars_map["X1"], vars_map["A"], vars_map["B"])
    AND(vars_map["X2"], vars_map["C"], vars_map["D"])
    OR(vars_map["X3"], vars_map["E"], vars_map["F"])
    NOT(vars_map["X4"], vars_map["G"])

    OR(vars_map["X5"], vars_map["X1"], vars_map["X2"])
    AND(vars_map["X6"], vars_map["X3"], vars_map["X4"])
    AND(vars_map["X7"], vars_map["X5"], vars_map["X6"])

    OR(vars_map["X8"], vars_map["H"], vars_map["I"])
    AND(vars_map["X9"], vars_map["X8"], vars_map["J"])

    NAND(vars_map["X10"], vars_map["A"], vars_map["C"])
    NOR(vars_map["X11"], vars_map["B"], vars_map["D"])

    OR(vars_map["Z_orig"], vars_map["X7"], vars_map["X9"])

    temp = new_var("temp1")
    OR(temp, vars_map["Z_orig"], vars_map["X10"])
    OR(vars_map["Z_ext"], temp, vars_map["X11"])

    # Force Z_ext = True
    cnf.append([vars_map["Z_ext"]])

    solver = Solver()
    solver.append_formula(cnf)

    results = []
    count = 0

    while solver.solve():
        model = solver.get_model()
        count += 1

        solution = {
            k: (model[vars_map[k] - 1] > 0)
            for k in ["A","B","C","D","E","F","G","H","I","J"]
        }

        results.append(solution)

        # Block this solution
        block = [-model[vars_map[k] - 1] for k in solution]
        solver.add_clause(block)

    return results, count

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run_sat', methods=['GET'])
def run_sat():
    results, count = solve_with_sat()

    return jsonify({
        "solutions": results,
        "total_solutions": count
    })

if __name__ == '__main__':
    app.run(debug=True)