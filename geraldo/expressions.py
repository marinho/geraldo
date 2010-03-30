# YET IN DEVELOPMENT

import re
from utils import get_attr_value

def run_expression(objects, expression):
    """Runs an expression for a given objects list"""
    return _interpreter.run_expression(objects, expression)

EXP_QUOTE = re.compile('[\'"].*?[\'"]')
EXP_MATH_OPERATORS = re.compile('.+[/\*\+\-].+')
EXP_CALL = re.compile('(.+)\((.*)\).*')
MATH_OPERATORS = ('*','/','+','-')

class Expression(object):
    """Compact and compile expression to compiled Python function, store it in
    _expressions and returns the function"""

    _expression = None
    _globals = {}

    def __new__(cls, expression):
        # Clean expression
        exp = expression.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Compacts expression
        _globals = {}
        exp2 = exp
        count = 0
        while '"' in exp2 or "'" in exp2:
            val = EXP_QUOTE.findall(exp2)[0]
            key = '_str'+str(count)
            count += 1

            _globals[key] = val
            exp2 = EXP_QUOTE.sub(key, exp2, 1)

        # Clean empty spaces
        exp2 = exp2.replace(' ', '')

        # Clean expression with strings
        exp = exp2
        for k,v in _globals.items():
            if k.startswith('_str'):
                exp = exp.replace(k,v)

        if exp in _expressions:
            obj = _expressions[exp]
            obj._globals = _globals
        else:
            obj = super(Expression, cls).__new__(cls)
            obj._expression = exp
            obj._globals =_globals

            _expressions[exp] = obj

        return obj

    def __init__(self, expression):
        # Transform tokens in a tree
        self._tokens = self.get_tokens()
        raise Exception(self._tokens)

    def execute(self, objects):
        return None

    def get_tokens(self, expression=None):
        expression = expression or self._expression
        nodes, temp, in_block = [], '', 0

        # Separes nodes
        for ch in expression:
            if ch == '(':
                in_block += 1
                temp += ch
            elif ch == ')':
                in_block -= 1
                temp += ch
            elif in_block == 0 and ch in MATH_OPERATORS:
                nodes.append(temp)
                nodes.append(ch)
                temp = ''
            else:
                temp += ch

        if temp:
            nodes.append(temp)

        # Transform child nodes to a tree
        def transf(node):
            if node.strip().startswith('"') or node.strip().startswith("'") or\
               not EXP_MATH_OPERATORS.match(node):
                return node
            else:
                m = EXP_CALL.match(node)
                return (m.group(1), self.get_tokens(m.group(2)))
        nodes = map(transf, nodes)

        return tuple(nodes)

class Interpreter(object):
    def run_expression(self, objects, expression):
        """Runs an expression for a given objects list"""
        return Expression(expression).execute(objects)

_interpreter = Interpreter()
_expressions = {}

