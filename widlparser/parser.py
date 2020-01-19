# coding=utf-8
#
#  Copyright © 2013 Hewlett-Packard Development Company, L.P.
#
#  This work is distributed under the W3C® Software License [1]
#  in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  [1] http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
#

import re
import itertools

from . import tokenizer
from .constructs import *


class Parser(object):
    def __init__(self, text = None, ui = None, symbol_table = None):
        self.ui = ui
        self.symbol_table = symbol_table if (symbol_table) else {}
        self.reset()
        if (text):
            self.parse(text)

    def reset(self):
        self.constructs = []

    @property
    def complexity_factor(self):
        complexity = 0
        for construct in self.constructs:
            complexity += construct.complexity_factor
        return complexity

    def parse(self, text):
        tokens = tokenizer.Tokenizer(text, self.ui)

        while (tokens.has_tokens()):
            if (Callback.peek(tokens)):
                self.constructs.append(Callback(tokens, parser = self))
            elif (Interface.peek(tokens)):
                self.constructs.append(Interface(tokens, parser = self))
            elif (Mixin.peek(tokens)):
                self.constructs.append(Mixin(tokens, parser = self))
            elif (Namespace.peek(tokens)):
                self.constructs.append(Namespace(tokens, parser = self))
            elif (Dictionary.peek(tokens)):
                self.constructs.append(Dictionary(tokens, parser = self))
            elif (Enum.peek(tokens)):
                self.constructs.append(Enum(tokens, parser = self))
            elif (Typedef.peek(tokens)):
                self.constructs.append(Typedef(tokens, parser = self))
            elif (Const.peek(tokens)):   # Legacy support (SVG spec)
                self.constructs.append(Const(tokens, parser = self))
            elif (ImplementsStatement.peek(tokens)):
                self.constructs.append(ImplementsStatement(tokens, parser = self))
            elif (IncludesStatement.peek(tokens)):
                self.constructs.append(IncludesStatement(tokens, parser = self))
            else:
                self.constructs.append(SyntaxError(tokens, None, parser = self))

    def __str__(self):
        return ''.join([str(construct) for construct in self.constructs])

    def __repr__(self):
        return '[Parser: ' + ''.join([(repr(construct) + '\n') for construct in self.constructs]) + ']'

    def __len__(self):
        return len(self.constructs)

    def keys(self):
        return [construct.name for construct in self.constructs]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for construct in self.constructs:
                if (key == construct.name):
                    return construct
            return None
        return self.constructs[key]

    def __bool__(self):
        return True

    def __iter__(self):
        return iter(self.constructs)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for construct in self.constructs:
                if (key == construct.name):
                    return True
            return False
        return (key in self.constructs)

    def add_type(self, type):
        self.symbol_table[type.name] = type

    def get_type(self, name):
        return self.symbol_table.get(name)

    def find(self, name):
        match = re.match('(.*)\(.*\)(.*)', name)    # strip ()'s
        while (match):
            name = match.group(1) + match.group(2)
            match = re.match('(.*)\(.*\)(.*)', name)

        path = None
        if ('/' in name):
            path = name.split('/')
        elif ('.' in name):
            path = name.split('.')

        if (path):
            construct_name = path[0]
            member_name = path[1]
            argument_name = path[2] if (2 < len(path)) else member_name
            for construct in reversed(self.constructs):
                if (construct_name == construct.name):
                    if (1 == len(path)):
                        return construct
                    for member in reversed(construct):
                        if (member_name == member.name):
                            if (2 < len(path)):
                                argument = member.find_argument(argument_name)
                                if (argument):
                                    return argument
                            else:
                                return member
                    else:
                        if (2 == len(path)):
                            argument = construct.find_argument(argument_name, False)
                            if (argument):
                                return argument
            return None

        for construct in reversed(self.constructs):
            if (name == construct.name):
                return construct

        # check inside top level constructs
        for construct in reversed(self.constructs):
            member = construct.find_member(name)
            if (member):
                return member

        # check argument names last
        for construct in reversed(self.constructs):
            argument = construct.find_argument(name)
            if (argument):
                return argument

        return None

    def find_all(self, name):
        match = re.match('(.*)\(.*\)(.*)', name)    # strip ()'s
        while (match):
            name = match.group(1) + match.group(2)
            match = re.match('(.*)\(.*\)(.*)', name)

        path = None
        if ('/' in name):
            path = name.split('/')
        elif ('.' in name):
            path = name.split('.')

        result = []

        if (path):
            construct_name = path[0]
            member_name = path[1]
            argument_name = path[2] if (2 < len(path)) else member_name
            for construct in self.constructs:
                if (construct_name == construct.name):
                    if (1 == len(path)):
                        result.append(construct)
                        continue
                    for member in construct:
                        if (member_name == member.name):
                            if (2 < len(path)):
                                argument = member.find_argument(argument_name)
                                if (argument):
                                    result.append(argument)
                            else:
                                result.append(member)
                    else:
                        if (2 == len(path)):
                            argument = construct.find_argument(argument_name, False)
                            if (argument):
                                result.append(argument)
            return result

        for construct in self.constructs:
            if (name == construct.name):
                result.append(construct)

        # check inside top level constructs
        for construct in self.constructs:
            result += construct.find_members(name)

        # check argument names last
        for construct in self.constructs:
            result += construct.find_arguments(name)

        return result

    def normalized_method_name(self, method_text, interface_name = None):
        match = re.match(r'(.*)\((.*)\)(.*)', method_text)
        if (match):
            tokens = tokenizer.Tokenizer(match.group(2))
            if (ArgumentList.peek(tokens)):
                arguments = ArgumentList(tokens, None)
                return match.group(1).strip() + '(' + arguments.argument_names[0] + ')'
            name = match.group(1).strip() + match.group(3)
            argument_names = [argument.strip() for argument in match.group(2).split(',')]
        else:
            name = method_text
            argument_names = None

        if (interface_name):
            interface = self.find(interface_name)
            if (interface):
                method = interface.find_method(name, argument_names)
                if (method):
                    return method.method_name
            return name + '(' + ', '.join(argument_names or []) + ')'

        for construct in self.constructs:
            method = construct.find_method(name, argument_names)
            if (method):
                return method.method_name

        construct = self.find(name)
        if (construct and ('method' == construct.idl_type)):
            return construct.method_name
        return name + '(' + ', '.join(argument_names or []) + ')'

    def normalized_method_names(self, method_text, interface_name = None):
        match = re.match(r'(.*)\((.*)\)(.*)', method_text)
        if (match):
            tokens = tokenizer.Tokenizer(match.group(2))
            if (ArgumentList.peek(tokens)):
                arguments = ArgumentList(tokens, None)
                return [match.group(1).strip() + '(' + argument_name + ')' for argument_name in arguments.argument_names]
            name = match.group(1).strip() + match.group(3)
            argument_names = [argument.strip() for argument in match.group(2).split(',')]
        else:
            name = method_text
            argument_names = None

        if (interface_name):
            interface = self.find(interface_name)
            if (interface):
                methods = interface.find_methods(name, argument_names)
                if (methods):
                    return list(itertools.chain(*[method.method_names for method in methods]))
            return [name + '(' + ', '.join(argument_names or []) + ')']

        for construct in self.constructs:
            methods = construct.find_methods(name, argument_names)
            if (methods):
                return list(itertools.chain(*[method.method_names for method in methods]))

        construct = self.find(name)
        if (construct and ('method' == construct.idl_type)):
            return construct.method_names
        return [name + '(' + ', '.join(argument_names or []) + ')']

    def markup(self, marker):
        if (marker):
            generator = MarkupGenerator(None)
            for construct in self.constructs:
                construct.markup(generator)
            return generator.markup(marker)
        return str(self)


