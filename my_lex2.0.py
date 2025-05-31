# ------------------------------------------------------------
# lex.py
#
# tokenizer for simple arm robot instructions
# ------------------------------------------------------------
import sys
import io
import re
from tabulate import tabulate
import traceback

RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'

lineno = 1
line_code = ""

COLORS = [
    RESET,
    BOLD,
    RED,
    GREEN,
    YELLOW,
    BLUE,
    MAGENTA,
    CYAN,
    WHITE,
]

def nameof(value) -> str:
    for name, val in globals().items():
        if val is value:
            return name
    return None


color_dict = dict(zip(COLORS, [
    nameof(c)
    for c in COLORS
]))

class Lexer:
    def __init__(self, rules, ignore="Espacio"):
        self.rules = [(re.compile(pattern), name) for pattern, name in rules]
        self.ignore = ignore

    def tokenize(self, text):
        pos = 0
        tokens = []
        while pos < len(text):
            match_found = False
            for pattern, token_name in self.rules:
                match = pattern.match(text, pos)
                if match:
                    if token_name not in self.ignore: 
                        tokens.append((token_name, match.group()))
                    pos = match.end()
                    match_found = True
                    break
            if not match_found:
                raise SyntaxError(f"Token inesperado en '{text[pos]}', {pos=}")
        return tokens
    
class Parser:
    def __init__(self, statements, lexer: Lexer):
        try:
            self.lexer = lexer
            self.statements = dict(statements)
        except Exception:
            print("Reglas invalidas")

    def parse(self, statement: str):
        p = None
        try:
            st = dict(self.lexer.tokenize(statement))
            struct = " ".join(st.keys()).strip()
            p = [""] + list(st.values())
            self.statements[struct](p)
        except (KeyError, ValueError) as err:
            self.statements["Error"](p)


class Robot:
    def __init__(self):
        self.velocidad = 0
        self.base = 0
        self.cuerpo = 0
        self.garra = 0
        self.init = False

    def set_value(self, name, value) -> None:
        if self.init:
            if   name == 'velocidad': self.velociddad = value
            elif name == 'base'     : self.base       = value
            elif name == 'cuerpo'   : self.cuerpo     = value
            elif name == 'garra'    : self.garra      = value
            print(f"{MAGENTA}{name} = {value}{RESET}")
        else: print(f"{RED}Inicialice el robot{RESET}")

    def action(self, name) -> None:
        if name == 'iniciar':
            self.init = True
            print(f"{BLUE}Iniciar robot{RESET}")
        if self.init:
            if name == 'cerrarGarra':
                print(f"{BLUE}Cerrar garra{RESET}")
            elif name == 'abrirGarra':
                print(f"{BLUE}Abrir garra{RESET}")
            elif name == 'print':
                print(f"{YELLOW}{self.__str__()}{RESET}")
        else: print(f"{RED}Inicialice el robot{RESET}")

    def __str__(self):
        return f"{self.velocidad=}, {self.base=}, {self.cuerpo=}, {self.garra=}"

def tabulate_tokens(code:str, colors:bool) -> dict:
    tokens = lexer.tokenize(code)

    if colors:
        headers = [f'{BLUE}Token{RESET}', f'{CYAN}Tipo{RESET}', f'{MAGENTA}Valor{RESET}', f'{RED}Parametro{RESET}']
    else:
        headers = ['Token', 'Tipo', 'Valor', 'Parametro']
    rows    = []

    for i, token in enumerate(tokens):
        type, token_name = token
        value = '-'
        parameter = '-'

        if type == 'Método':
            value = int(tokens[i+2][1])
            parameter = 'Si'

        if type not in ('Espacio', 'Salto de linea'):
            if colors:
                rows.append([f'{BLUE}{token_name}{RESET}', f'{CYAN}{type}{RESET}', f'{MAGENTA}{value}{RESET}', f'{RED}{parameter}{RESET}'])
            else:
                rows.append([token_name, type, value, parameter])
    return {
        'headers': headers,
        'rows': rows
    }


RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'

# List of token names.   This is always required
TOKEN_PATTERNS = [
    # (Token, Tipo, Valor, Parametro)
    ('\n', 'Salto_de_linea'), # Salto de linea
    ('Robot', 'Palabra_r'), # inicializar un robot
    ('(b|r)[0-9]', 'Identificador'),
    ('\.', 'Punto'),
    ('base|cuerpo|garra|velocidad', 'Metodo'),
    ('iniciar|cerrarGarra|abrirGarra', 'Accion'),
    ('=', 'Operador'),
    ('(360|3[0-5][0-9]|[12]\d\d|\d\d|\d)', 'Valor'),
    (' ', 'Espacio'),
    ('\(', 'IParentesis'),
    ('\)', 'DParentesis'),
    ('repetir', 'IBucle'),
    ('finRepetir', 'FBucle'),
    ('.', 'Carácter ilegal')
]

# Build the lexer
lexer = Lexer(TOKEN_PATTERNS, ignore=("Espacio", "Salto_de_linea"))


# ------------ Rules ------------

robots = dict()
loop = False
rt = 0
instructions = []

def p_statement_instance(p):
    robots[p[2]] = Robot()

def p_statement_method(p):
    global loop
    try:
        robots[p[1]].set_value(p[3], int(p[5]))
        if loop: 
            instructions.append((p[1], p[3], p[5]))

    except (LookupError, KeyError, ValueError):
        print("Undefined name '%s'" % p[1])


def p_statement_action(p):
    global loop
    try:
        robots[p[1]].action(p[3])
    except KeyError:
        print(f"{RED}Robot not declared {p}{RESET}")
    if loop:
        instructions.append((p[1], p[3], None))

def p_statement_begin_loop(p):
    global loop, rt
    loop = True
    rt = int(p[5])
    instructions.clear()

def p_statement_end_loop(p):
    global loop, rt
    loop = False
    for _ in range(rt-1):
        for id, func, val in instructions:
            if val:
                robots[id].set_value(func, val)
            else:
                robots[id].action(func)
    rt = 0
    

def p_statement_newline(p):
    pass

def p_error(p):
    global lineno, line_code
    val = "".join(p) if p else line_code
    if len(val) == 0: return
    print(f"{RED}Error sintáctico en la línea {lineno} [{val}]{RESET}")


# Rules and instructions
STATEMENTS = [
    ("Palabra_r Identificador", p_statement_instance),
    ("Identificador Punto Metodo IParentesis Valor DParentesis", p_statement_method),
    ("Identificador Punto Metodo Operador Valor", p_statement_method),
    ("Identificador Punto Accion IParentesis DParentesis", p_statement_action),
    ("Identificador Punto IBucle IParentesis Valor DParentesis", p_statement_begin_loop),
    ("Identificador Punto FBucle IParentesis DParentesis", p_statement_end_loop),
    ("newline", p_statement_newline),
    ("Error", p_error)
]

parser = Parser(STATEMENTS, lexer)

def format_color(color:str) -> str:
    if color == RESET: return "</span>"
    else:
        try:
            return f'<span style="color: {color_dict[color].lower()};">'
        except KeyError:
            return '<span style="color: white;">'

def remove_color(s:str, format=False):
    colors = (re.findall("(\\033\[(\d|\d\d)m)", s))

    for color in colors:
        new_color = ""
        if format: new_color = format_color(color[0])
        s = s.replace(color[0], new_color)
    
    return f"<br>{s}</br>"

def execute(code:str, plain=True, format=False) -> str:
    global lineno, line_code
    lineno = 1

    buffer = io.StringIO()
    sys.stdout = buffer
    for inst in code.split('\n'):
        line_code = inst
        if len(inst.strip()) > 0:
            try:
                inst
            except SyntaxError:
                break
            parser.parse(inst)
        lineno += 1
    sys.stdout = sys.__stdout__

    buff = buffer.getvalue()
    output = []
    if plain:
        for line in buff.split("\n"):
            output.append(remove_color(line, format))
    else:
        for line in buff.split("\n"):
            output.append(line)

    buffer.close()
    return '\n'.join(output)


if __name__ == '__main__':
    code1 = """
    Robot b1
    b1.iniciar()
    b1.repetir(2)
    b1.velocidad(50)
    b1.base(180)
    b1.cuerpo(45)
    b1.garra(0)
    b1.cuerpo(90)
    b1.garra(90)
    b1.cerrarGarra()
    b1.abrirGarra()
    b1.finRepetir()
    """

    print(execute(code1, plain=False))

