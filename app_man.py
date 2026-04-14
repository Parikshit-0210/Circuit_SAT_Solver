from flask import Flask, render_template, jsonify

app = Flask(__name__)

cnf = []

vars_map = {}
counter = 1

def new_var(name):
    global counter
    vars_map[name] = counter
    counter += 1
    return vars_map[name]

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

def build_cnf():
    global cnf, vars_map, counter
    cnf = []
    vars_map = {}
    counter = 1

    for v in ["A","B","C","D","E","F","G","H","I","J",
              "X1","X2","X3","X4","X5","X6","X7","X8","X9","X10","X11",
              "Z_orig","Z_ext"]:
        new_var(v)

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

def is_satisfied(clause, assignment):
    for lit in clause:
        var = abs(lit)
        val = assignment.get(var)

        if val is None:
            continue

        if (lit > 0 and val) or (lit < 0 and not val):
            return True
    return False

def is_conflict(clause, assignment):
    for lit in clause:
        var = abs(lit)
        val = assignment.get(var)

        if val is None:
            return False

        if (lit > 0 and val) or (lit < 0 and not val):
            return False
    return True

def dpll(assignment, variables):
    # Check all clauses
    for clause in cnf:
        if is_conflict(clause, assignment):
            return None

    if len(assignment) == len(variables):
        return assignment

    # Pick unassigned variable
    for var in variables:
        if var not in assignment:
            break

    # Try True
    assignment[var] = True
    result = dpll(assignment.copy(), variables)
    if result:
        return result

    # Try False
    assignment[var] = False
    result = dpll(assignment.copy(), variables)
    if result:
        return result

    return None

def find_all_solutions():
    build_cnf()

    variables = list(vars_map.values())
    solutions = []

    def backtrack(assignment):
        for clause in cnf:
            if is_conflict(clause, assignment):
                return

        if len(assignment) == len(variables):
            solutions.append(assignment.copy())
            return

        for var in variables:
            if var not in assignment:
                break

        assignment[var] = True
        backtrack(assignment)
        assignment[var] = False
        backtrack(assignment)
        del assignment[var]

    backtrack({})

    readable = []
    for sol in solutions:
        readable.append({
            k: sol[vars_map[k]]
            for k in ["A","B","C","D","E","F","G","H","I","J"]
        })

    return readable, len(readable)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_sat')
def run_sat():
    results, count = find_all_solutions()

    return jsonify({
        "solutions": results,
        "total_solutions": count
    })

if __name__ == '__main__':
    app.run(debug=True)