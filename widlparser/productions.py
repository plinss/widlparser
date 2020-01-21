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
"""Basic language productions for WebIDL."""


import itertools

from . import constructs, tokenizer


def _name(thing):
    return thing.name if (thing) else ''


class Production(object):
    """
    Base class for all productions.

    Consumes leading and optionally trailing whitespace,
    also may consume following semicolon.
    """

    def __init__(self, tokens):
        self._leading_space = self._whitespace(tokens)
        self._tail = None
        self._semicolon = ''

    def _did_parse(self, tokens, include_trailing_space = True):
        self._trailing_space = self._whitespace(tokens) if (include_trailing_space) else ''

    def _whitespace(self, tokens):
        whitespace = tokens.whitespace()
        return whitespace.text if (whitespace) else ''

    def __str__(self):
        output = self._leading_space + self._str()
        output += ''.join([str(token) for token in self._tail]) if (self._tail) else ''
        return output + str(self._semicolon) + self._trailing_space

    def _markup(self, generator):
        generator.add_text(self._str())
        return self

    def markup(self, generator):
        generator.add_text(self._leading_space)
        target = self._markup(generator)
        if (target._tail):
            generator.add_text(''.join([str(token) for token in target._tail]))
        generator.add_text(str(target._semicolon))
        if (self != target):
            generator.add_text(target._trailing_space)
        generator.add_text(self._trailing_space)

    def _consume_semicolon(self, tokens, consume_tail = True):
        if (Symbol.peek(tokens, ';')):
            self._semicolon = Symbol(tokens, ';', False)
        elif (not Symbol.peek(tokens, '}')):
            if (consume_tail):
                skipped = tokens.syntax_error((';', '}'))
                if (0 < len(skipped)):
                    self._tail = skipped[:-1]
                    tokens.restore(skipped[-1])
                    self._semicolon = Symbol(tokens, ';', False) if (Symbol.peek(tokens, ';')) else ''
            else:
                tokens.syntax_error(None)
        else:
            tokens.syntax_error(None)


class String(Production):
    """
    String production.

    Syntax:
    <string-token>
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and token.is_string())

    def __init__(self, tokens, include_trailing_space = True):
        Production.__init__(self, tokens)
        self.string = tokens.next().text
        self._did_parse(tokens, include_trailing_space)

    def _str(self):
        return self.string

    def _markup(self, generator):
        generator.add_text(self.string)
        return self

    def __repr__(self):
        return self.string


class Symbol(Production):
    """
    String production.

    Syntax:
    <symbol-token>
    """

    @classmethod
    def peek(cls, tokens, symbol=None):
        token = tokens.push_position()
        return tokens.pop_position(token and token.is_symbol(symbol))

    def __init__(self, tokens, symbol = None, include_trailing_space = True):
        Production.__init__(self, tokens)
        self.symbol = tokens.next().text
        if (symbol):
            assert(self.symbol == symbol)
        self._did_parse(tokens, include_trailing_space)

    def _str(self):
        return self.symbol

    def _markup(self, generator):
        if (self.symbol in tokenizer.Tokenizer.SYMBOL_IDENTS):
            generator.add_keyword(self.symbol)
        else:
            generator.add_text(self.symbol)
        return self

    def __repr__(self):
        return self.symbol


class IntegerType(Production):
    """
    Integer type production.

    Syntax:
    "short" | "long" ["long"]
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        if (token and token.is_symbol()):
            if ('long' == token.text):
                token = tokens.push_position()
                tokens.pop_position(token and token.is_symbol('long'))
                return tokens.pop_position(True)
            return tokens.pop_position('short' == token.text)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._space = None
        token = tokens.next()
        if ('long' == token.text):
            self.type = 'long'
            token = tokens.sneak_peek()
            if (token and token.is_symbol('long')):
                self._space = self._whitespace(tokens)
                self.type += ' ' + tokens.next().text
        else:
            self.type = token.text
        self._did_parse(tokens, False)

    def _str(self):
        if (self._space):
            return self._space.join(self.type.split(' '))
        return self.type

    def _markup(self, generator):
        if (self._space):
            keywords = self.type.split(' ')
            generator.add_keyword(keywords[0])
            generator.add_text(self._space)
            generator.add_keyword(keywords[1])
        else:
            generator.add_keyword(self.type)
        return self

    def __repr__(self):
        return '[IntegerType: ' + self.type + ']'


class UnsignedIntegerType(Production):
    """
    Unsigned integer type production.

    Syntax:
    "unsigned" IntegerType | IntegerType
    """

    @classmethod
    def peek(cls, tokens):
        if (IntegerType.peek(tokens)):
            return True
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'unsigned')):
            return tokens.pop_position(IntegerType.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.unsigned = Symbol(tokens, 'unsigned') if (Symbol.peek(tokens, 'unsigned')) else None
        self.type = IntegerType(tokens)
        self._did_parse(tokens, False)

    def _str(self):
        return (str(self.unsigned) + self.type._str()) if (self.unsigned) else self.type._str()

    def _markup(self, generator):
        if (self.unsigned):
            self.unsigned.markup(generator)
        return self.type._markup(generator)

    def __repr__(self):
        return '[UnsignedIntegerType: ' + ('[unsigned]' if (self.unsigned) else '') + repr(self.type) + ']'


class FloatType(Production):
    """
    Float type production.

    Syntax:
    "float" | "double"
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and (token.is_symbol('float') or token.is_symbol('double')))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        token = tokens.next()
        self.type = token.text
        self._did_parse(tokens, False)

    def _str(self):
        return self.type

    def _markup(self, generator):
        generator.add_keyword(self.type)
        return self

    def __repr__(self):
        return '[FloatType: ' + self.type + ']'


class UnrestrictedFloatType(Production):
    """
    Unrestricted float type production.

    Syntax:
    "unrestricted" FloatType | FloatType
    """

    @classmethod
    def peek(cls, tokens):
        if (FloatType.peek(tokens)):
            return True
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'unrestricted')):
            return tokens.pop_position(FloatType.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.unrestricted = Symbol(tokens, 'unrestricted') if (Symbol.peek(tokens, 'unrestricted')) else None
        self.type = FloatType(tokens)
        self._did_parse(tokens, False)

    def _str(self):
        return (str(self.unrestricted) + str(self.type)) if (self.unrestricted) else str(self.type)

    def _markup(self, generator):
        if (self.unrestricted):
            self.unrestricted.markup(generator)
        return self.type._markup(generator)

    def __repr__(self):
        return '[UnrestrictedFloatType: ' + ('[unrestricted]' if (self.unrestricted) else '') + repr(self.type) + ']'


class PrimitiveType(Production):
    """
    Primitive type production.

    Syntax:
    UnsignedIntegerType | UnrestrictedFloatType | "boolean" | "byte" | "octet"
    """

    @classmethod
    def peek(cls, tokens):
        return (UnsignedIntegerType.peek(tokens) or UnrestrictedFloatType.peek(tokens) or Symbol.peek(tokens, ('boolean', 'byte', 'octet')))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (UnsignedIntegerType.peek(tokens)):
            self.type = UnsignedIntegerType(tokens)
        elif (UnrestrictedFloatType.peek(tokens)):
            self.type = UnrestrictedFloatType(tokens)
        else:
            self.type = Symbol(tokens, None, False)
        self._did_parse(tokens, False)

    @property
    def type_name(self):
        return str(self.type)

    def _str(self):
        return self.type._str()

    def _markup(self, generator):
        return self.type._markup(generator)

    def __repr__(self):
        return '[PrimitiveType: ' + repr(self.type) + ']'


class Identifier(Production):
    """
    Identifier production.

    Syntax:
    <identifier-token>
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position(True)
        return tokens.pop_position(token and token.is_identifier())

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._name = tokens.next().text
        self._did_parse(tokens, False)

    @property
    def name(self):
        return self._name[1:] if ('_' == self._name[0]) else self._name

    def _str(self):
        return str(self._name)

    def _markup(self, generator):
        generator.add_name(self._name)
        return self

    def __repr__(self):
        return self._name


class TypeIdentifier(Production):
    """
    Type identifier production.

    Syntax:
    <identifier-token>
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position(True)
        return tokens.pop_position(token and token.is_identifier())

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._name = tokens.next().text
        self._did_parse(tokens, False)

    @property
    def name(self):
        return self._name[1:] if ('_' == self._name[0]) else self._name

    def _str(self):
        return str(self._name)

    def _markup(self, generator):
        generator.add_type_name(self._name)
        return self

    def __repr__(self):
        return self._name


class ConstType(Production):
    """
    Const type production.

    Syntax:
    PrimitiveType [Null] | Identifier [Null]
    """

    @classmethod
    def peek(cls, tokens):
        if (PrimitiveType.peek(tokens)):
            Symbol.peek(tokens, '?')
            return True
        tokens.push_position(False)
        if (TypeIdentifier.peek(tokens)):
            Symbol.peek(tokens, '?')
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (PrimitiveType.peek(tokens)):
            self.type = PrimitiveType(tokens)
            self.type_name = self.type.type_name
        else:
            self.type = TypeIdentifier(tokens)
            self.type_name = self.type.name
        self.null = Symbol(tokens, '?', False) if (Symbol.peek(tokens, '?')) else None
        self._did_parse(tokens)

    def _str(self):
        return str(self.type) + (str(self.null) if (self.null) else '')

    def _markup(self, generator):
        if (isinstance(self.type, TypeIdentifier)):
            self.type.markup(generator)
            if (self.null):
                generator.add_text(self.null)
                return self.null
            return self
        generator.add_primitive_type(self.type)
        if (self.null):
            self.null.markup(generator)
        return self

    def __repr__(self):
        return '[ConstType: ' + repr(self.type) + (' [null]' if (self.null) else '') + ']'


class FloatLiteral(Production):
    """
    Float literal production.

    Syntax:
    <float-token> | "-Infinity" | "Infinity" | "NaN"
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        if (token and token.is_float()):
            return tokens.pop_position(True)
        return tokens.pop_position(token and token.is_symbol(('-Infinity', 'Infinity', 'NaN')))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.value = tokens.next().text
        self._did_parse(tokens)

    def _str(self):
        return self.value

    def _markup(self, generator):
        if (self.value in tokenizer.Tokenizer.SYMBOL_IDENTS):
            generator.add_keyword(self.value)
        else:
            generator.add_text(self.value)
        return self

    def __repr__(self):
        return '[FloatLiteral: ' + self.value + ']'


class ConstValue(Production):
    """
    Const value production.

    Syntax:
    "true" | "false" | FloatLiteral | <integer-token> | "null"
    """

    @classmethod
    def peek(cls, tokens):
        if (FloatLiteral.peek(tokens)):
            return True
        token = tokens.push_position()
        return tokens.pop_position(token and (token.is_symbol(('true', 'false', 'null')) or token.is_integer()))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (FloatLiteral.peek(tokens)):
            self.value = FloatLiteral(tokens)
        elif (Symbol.peek(tokens)):
            self.value = Symbol(tokens, None, False)
        else:
            self.value = tokens.next().text
        self._did_parse(tokens)

    def _str(self):
        return str(self.value)

    def _markup(self, generator):
        if (isinstance(self.value, str)):
            if (self.value in tokenizer.Tokenizer.SYMBOL_IDENTS):
                generator.add_keyword(self.value)
            else:
                generator.add_text(self.value)
            return self
        return self.value._markup(generator)

    def __repr__(self):
        return '[ConstValue: ' + repr(self.value) + ']'


class EnumValue(Production):
    """
    Enum value production.

    Syntax:
    <string-token>
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and token.is_string())

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.value = tokens.next().text
        self._did_parse(tokens)

    def _markup(self, generator):
        generator.add_enum_value(self.value)
        return self

    def _str(self):
        return self.value

    def __repr__(self):
        return '[EnumValue: ' + self.value + ']'


class EnumValueList(Production):
    """
    Enum value list production.

    Syntax:
    EnumValue ["," EnumValue]... [","]
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (EnumValue.peek(tokens)):
            token = tokens.push_position()
            if (token and token.is_symbol(',')):
                token = tokens.sneak_peek()
                if (token and token.is_symbol('}')):
                    return tokens.pop_position(tokens.pop_position(True))
                return tokens.pop_position(tokens.pop_position(EnumValueList.peek(tokens)))
            tokens.pop_position(False)
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.values = []
        self._commas = []
        while (tokens.has_tokens()):
            self.values.append(EnumValue(tokens))
            if (Symbol.peek(tokens, ',')):
                self._commas.append(Symbol(tokens, ','))
                token = tokens.sneak_peek()
                if ((not token) or token.is_symbol('}')):
                    tokens.did_ignore(',')
                    break
                continue
            break
        self._did_parse(tokens)

    def _markup(self, generator):
        for value, _comma in itertools.zip_longest(self.values, self._commas, fillvalue = ''):
            value.markup(generator)
            if (_comma):
                _comma.markup(generator)
        return self

    def _str(self):
        return ''.join([str(value) + str(comma) for value, comma in itertools.zip_longest(self.values, self._commas, fillvalue = '')])

    def __repr__(self):
        return '[EnumValueList: ' + ''.join([repr(value) for value in self.values]) + ']'


class TypeSuffix(Production):
    """
    Type suffix production.

    Syntax:
    "[" "]" [TypeSuffix] | "?" [TypeSuffixStartingWithArray]
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, '[')):
            if (Symbol.peek(tokens, ']')):
                TypeSuffix.peek(tokens)
                return tokens.pop_position(True)
        elif (Symbol.peek(tokens, '?')):
            TypeSuffixStartingWithArray.peek(tokens)
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (Symbol.peek(tokens, '[')):
            self._open_bracket = Symbol(tokens, '[')
            self._close_bracket = Symbol(tokens, ']', False)
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
            self.array = True
            self.null = None
        else:
            self.null = Symbol(tokens, '?', False)
            self.suffix = TypeSuffixStartingWithArray(tokens) if (TypeSuffixStartingWithArray.peek(tokens)) else None
            self.array = False
            self._open_bracket = None
            self._close_bracket = None
        self._did_parse(tokens, False)

    def _str(self):
        output = (str(self._open_bracket) + str(self._close_bracket)) if (self.array) else ''
        output += str(self.null) if (self.null) else ''
        return output + (str(self.suffix) if (self.suffix) else '')

    def __repr__(self):
        output = '[TypeSuffix: ' + ('[array] ' if (self.array) else '') + ('[null] ' if (self.null) else '')
        return output + (repr(self.suffix) if (self.suffix) else '') + ']'


class TypeSuffixStartingWithArray(Production):
    """
    Type suffix starting with array production.

    Syntax:
    "[" "]" [TypeSuffix]
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, '[')):
            if (Symbol.peek(tokens, ']')):
                TypeSuffix.peek(tokens)
                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._open_bracket = Symbol(tokens, '[')
        self._close_bracket = Symbol(tokens, ']', False)
        self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        self._did_parse(tokens, False)

    def _str(self):
        return str(self._open_bracket) + str(self._close_bracket) + (str(self.suffix) if (self.suffix) else '')

    def __repr__(self):
        return '[TypeSuffixStartingWithArray: ' + (repr(self.suffix) if (self.suffix) else '') + ']'


class SingleType(Production):
    """
    Single type production.

    Syntax:
    NonAnyType | "any" [TypeSuffixStartingWithArray]
    """

    @classmethod
    def peek(cls, tokens):
        if (NonAnyType.peek(tokens)):
            return True
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'any')):
            TypeSuffixStartingWithArray.peek(tokens)
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (NonAnyType.peek(tokens)):
            self.type = NonAnyType(tokens)
            self.type_name = self.type.type_name
            self.suffix = None
        else:
            self.type = Symbol(tokens, 'any', False)
            self.type_name = None
            self.suffix = TypeSuffixStartingWithArray(tokens) if (TypeSuffixStartingWithArray.peek(tokens)) else None
        self._did_parse(tokens, False)

    @property
    def type_names(self):
        return [self.type_name]

    def _str(self):
        return str(self.type) + (str(self.suffix) if (self.suffix) else '')

    def _markup(self, generator):
        self.type._markup(generator)
        if (self.suffix):
            self.suffix.markup(generator)
        return self

    def __repr__(self):
        return '[SingleType: ' + repr(self.type) + (repr(self.suffix) if (self.suffix) else '') + ']'


class NonAnyType(Production):
    """
    Non-any type production.

    Syntax:
    PrimitiveType [TypeSuffix] | "ByteString" [TypeSuffix] | "DOMString" [TypeSuffix]
    | "USVString" TypeSuffix | Identifier [TypeSuffix] | "sequence" "<" TypeWithExtendedAttributes ">" [Null]
    | "object" [TypeSuffix] | "Error" TypeSuffix | "Promise" "<" ReturnType ">" [Null] | BufferRelatedType [Null]
    | "FrozenArray" "<" TypeWithExtendedAttributes ">" [Null] | "record" "<" StringType "," TypeWithExtendedAttributes ">"
    """

    BUFFER_RELATED_TYPES = frozenset(['ArrayBuffer', 'DataView', 'Int8Array', 'Int16Array', 'Int32Array',
                                      'Uint8Array', 'Uint16Array', 'Uint32Array', 'Uint8ClampedArray',
                                      'Float32Array', 'Float64Array'])
    STRING_TYPES = frozenset(['ByteString', 'DOMString', 'USVString'])
    OBJECT_TYPES = frozenset(['object', 'Error'])

    @classmethod
    def peek(cls, tokens):
        if (PrimitiveType.peek(tokens)):
            TypeSuffix.peek(tokens)
            return True
        token = tokens.push_position()
        if (token and (token.is_symbol(cls.STRING_TYPES | cls.OBJECT_TYPES) or token.is_identifier())):
            TypeSuffix.peek(tokens)
            return tokens.pop_position(True)
        elif (token and token.is_symbol(('sequence', 'FrozenArray'))):
            if (Symbol.peek(tokens, '<')):
                if (TypeWithExtendedAttributes.peek(tokens)):
                    if (Symbol.peek(tokens, '>')):
                        Symbol.peek(tokens, '?')
                        return tokens.pop_position(True)
        elif (token and token.is_symbol('Promise')):
            if (Symbol.peek(tokens, '<')):
                if (ReturnType.peek(tokens)):
                    if (Symbol.peek(tokens, '>')):
                        Symbol.peek(tokens, '?')
                        return tokens.pop_position(True)
        elif (token and token.is_symbol(cls.BUFFER_RELATED_TYPES)):
            Symbol.peek(tokens, '?')
            return tokens.pop_position(True)
        elif (token and token.is_symbol('record')):
            if (Symbol.peek(tokens, '<')):
                if (Symbol.peek(tokens, cls.STRING_TYPES)):
                    if (Symbol.peek(tokens, ',')):
                        if (TypeWithExtendedAttributes.peek(tokens)):
                            if (Symbol.peek(tokens, '>')):
                                Symbol.peek(tokens, '?')
                                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.sequence = None
        self.promise = None
        self.record = None
        self._open_type = None
        self._close_type = None
        self.null = False
        self.suffix = None
        self.type_name = None
        self.key_type = None
        if (PrimitiveType.peek(tokens)):
            self.type = PrimitiveType(tokens)
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        else:
            token = tokens.sneak_peek()
            if (token.is_identifier()):
                self.type = TypeIdentifier(tokens)
                self.type_name = self.type.name
                self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
            elif (token.is_symbol(('sequence', 'FrozenArray'))):
                self.sequence = Symbol(tokens)
                self._open_type = Symbol(tokens, '<')
                self.type = TypeWithExtendedAttributes(tokens)
                self._close_type = Symbol(tokens, '>', False)
                self.null = Symbol(tokens, '?', False) if (Symbol.peek(tokens, '?')) else None
            elif (token.is_symbol('Promise')):
                self.promise = Symbol(tokens, 'Promise')
                self._open_type = Symbol(tokens, '<')
                self.type = ReturnType(tokens)
                self._close_type = Symbol(tokens, '>', False)
                self.null = Symbol(tokens, '?', False) if (Symbol.peek(tokens, '?')) else None
            elif (token.is_symbol(self.BUFFER_RELATED_TYPES)):
                self.type = Symbol(tokens, None, False)
                self.null = Symbol(tokens, '?', False) if (Symbol.peek(tokens, '?')) else None
            elif (token.is_symbol('record')):
                self.record = Symbol(tokens)
                self._open_type = Symbol(tokens, '<')
                self.key_type = Symbol(tokens)
                self._comma = Symbol(tokens, ',')
                self.type = TypeWithExtendedAttributes(tokens)
                self._close_type = Symbol(tokens, '>', False)
                self.null = Symbol(tokens, '?', False) if (Symbol.peek(tokens, '?')) else None
            else:
                self.type = Symbol(tokens, None, False)  # string or object
                self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        self._did_parse(tokens, False)

    def _str(self):
        if (self.sequence):
            output = str(self.sequence) + str(self._open_type) + str(self.type) + str(self._close_type)
            return output + (str(self.null) if (self.null) else '')
        if (self.promise):
            output = str(self.promise) + str(self._open_type) + str(self.type) + str(self._close_type)
            return output + (str(self.null) if (self.null) else '')
        if (self.record):
            output = str(self.record) + str(self._open_type) + str(self.key_type) + str(self._comma) + str(self.type) + str(self._close_type)
            return output + (str(self.null) if (self.null) else '')

        output = str(self.type)
        output = output + (str(self.null) if (self.null) else '')
        return output + (str(self.suffix) if (self.suffix) else '')

    def _markup(self, generator):
        if (self.sequence):
            self.sequence.markup(generator)
            generator.add_text(self._open_type)
            generator.add_type(self.type)
            generator.add_text(self._close_type)
            generator.add_text(self.null)
            return self
        if (self.promise):
            self.promise.markup(generator)
            generator.add_text(self._open_type)
            self.type.markup(generator)
            generator.add_text(self._close_type)
            generator.add_text(self.null)
            return self
        if (self.record):
            self.record.markup(generator)
            generator.add_text(self._open_type)
            generator.add_string_type(self.key_type)
            generator.add_text(self._comma)
            self.type.markup(generator)
            generator.add_text(self._close_type)
            generator.add_text(self.null)
            return self
        if (isinstance(self.type, TypeIdentifier)):
            self.type.markup(generator)
            if (self.suffix):
                self.suffix.markup(generator)
            return self
        if (isinstance(self.type, PrimitiveType)):
            generator.add_primitive_type(self.type)
        elif (isinstance(self.type, Symbol)):
            if (self.type.symbol in self.BUFFER_RELATED_TYPES):
                generator.add_buffer_type(self.type)
            elif (self.type.symbol in self.STRING_TYPES):
                generator.add_string_type(self.type)
            elif (self.type.symbol in self.OBJECT_TYPES):
                generator.add_object_type(self.type)
            else:
                assert(False)
        else:
            self.type._markup(generator)
        generator.add_text(self.null)
        if (self.suffix):
            self.suffix.markup(generator)
        return self

    def __repr__(self):
        output = ('[NonAnyType: ' + ('[sequence] ' if (self.sequence) else '') + ('[Promise] ' if (self.promise) else '')
                  + ('[record] [StringType: ' + repr(self.key_type) + '] ' if (self.record) else ''))
        output += repr(self.type) + ('[null]' if (self.null) else '')
        return output + (repr(self.suffix) if (self.suffix) else '') + ']'


class UnionMemberType(Production):
    """
    Union member type production.

    Syntax:
    [ExtendedAttributeList] NonAnyType | UnionType [TypeSuffix] | "any" "[" "]" [TypeSuffix]
    """

    @classmethod
    def peek(cls, tokens):
        if (ExtendedAttributeList.peek(tokens)):
            if (NonAnyType.peek(tokens)):
                return True
        if (NonAnyType.peek(tokens)):
            return True
        if (UnionType.peek(tokens)):
            TypeSuffix.peek(tokens)
            return True
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'any')):
            if (Symbol.peek(tokens, '[')):
                if (Symbol.peek(tokens, ']')):
                    TypeSuffix.peek(tokens)
                    return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.any = None
        self._open_bracket = None
        self._close_bracket = None
        self.type_name = None
        self._extended_attributes = ExtendedAttributeList(tokens, self) if (ExtendedAttributeList.peek(tokens)) else None
        if (NonAnyType.peek(tokens)):
            self.type = NonAnyType(tokens)
            self.suffix = None
            self.type_name = self.type.type_name
        elif (UnionType.peek(tokens)):
            self.type = UnionType(tokens)
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        else:
            self.any = Symbol(tokens, 'any')
            self._open_bracket = Symbol(tokens, '[')
            self._close_bracket = Symbol(tokens, ']')
            self.type = 'any[]'
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        self._did_parse(tokens, False)

    @property
    def extended_attributes(self):
        return self._extended_attributes if (self._extended_attributes) else {}

    def _str(self):
        output = str(self._extended_attributes) if (self._extended_attributes) else ''
        output += (str(self.any) + str(self._open_bracket) + str(self._close_bracket)) if (self.any) else str(self.type)
        return output + (str(self.suffix) if (self.suffix) else '')

    def _markup(self, generator):
        if (self.any):
            self.any.markup(generator)
            generator.add_text(self._open_bracket)
            generator.add_text(self._close_bracket)
        else:
            if (self._extended_attributes):
                self._extended_attributes.markup(generator)
            self.type.markup(generator)
        generator.add_text(self.suffix)
        return self

    def __repr__(self):
        output = '[UnionMemberType: ' + ('[any[]]' if (self.any) else repr(self.type))
        return output + (repr(self.suffix) if (self.suffix) else '') + ']'


class UnionType(Production):
    """
    Union member type production.

    Syntax:
    "(" UnionMemberType ["or" UnionMemberType]... ")"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, '(')):
            while (tokens.has_tokens()):
                if (UnionMemberType.peek(tokens)):
                    token = tokens.peek()
                    if (token and token.is_symbol('or')):
                        continue
                    if (token and token.is_symbol(')')):
                        return tokens.pop_position(True)
                return tokens.pop_position(False)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._open_paren = Symbol(tokens, '(')
        self.types = []
        self._ors = []
        while (tokens.has_tokens()):
            self.types.append(UnionMemberType(tokens))
            token = tokens.sneak_peek()
            if (token and token.is_symbol()):
                if ('or' == token.text):
                    self._ors.append(Symbol(tokens, 'or'))
                    continue
                elif (')' == token.text):
                    break
            break
        self._close_paren = Symbol(tokens, ')', False)
        self._did_parse(tokens, False)

    @property
    def type_names(self):
        return [type.type_name for type in self.types]

    def _str(self):
        output = str(self._open_paren)
        output += ''.join([str(type) + str(_or) for type, _or in itertools.zip_longest(self.types, self._ors, fillvalue = '')])
        return output + str(self._close_paren)

    def _markup(self, generator):
        generator.add_text(self._open_paren)
        for type, _or in itertools.zip_longest(self.types, self._ors, fillvalue = ''):
            generator.add_type(type)
            if (_or):
                _or.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        return '[UnionType: ' + ''.join([repr(type) for type in self.types]) + ']'


class Type(Production):
    """
    Type production.

    Syntax:
    SingleType | UnionType [TypeSuffix]
    """

    @classmethod
    def peek(cls, tokens):
        if (SingleType.peek(tokens)):
            return True
        if (UnionType.peek(tokens)):
            TypeSuffix.peek(tokens)
            return True
        return False

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        if (SingleType.peek(tokens)):
            self.type = SingleType(tokens)
            self.suffix = None
        else:
            self.type = UnionType(tokens)
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        self._did_parse(tokens)

    @property
    def type_names(self):
        return self.type.type_names

    def _str(self):
        return str(self.type) + (self.suffix._str() if (self.suffix) else '')

    def _markup(self, generator):
        self.type.markup(generator)
        generator.add_text(self.suffix)
        return self

    def __repr__(self):
        return '[Type: ' + repr(self.type) + (repr(self.suffix) if (self.suffix) else '') + ']'


class TypeWithExtendedAttributes(Production):
    """
    Type with extended attributes production.

    Syntax:
    [ExtendedAttributeList] SingleType | UnionType [TypeSuffix]
    """

    @classmethod
    def peek(cls, tokens):
        ExtendedAttributeList.peek(tokens)
        if (SingleType.peek(tokens)):
            return True
        if (UnionType.peek(tokens)):
            TypeSuffix.peek(tokens)
            return True
        return False

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._extended_attributes = ExtendedAttributeList(tokens, self) if (ExtendedAttributeList.peek(tokens)) else None
        if (SingleType.peek(tokens)):
            self.type = SingleType(tokens)
            self.suffix = None
        else:
            self.type = UnionType(tokens)
            self.suffix = TypeSuffix(tokens) if (TypeSuffix.peek(tokens)) else None
        self._did_parse(tokens)

    @property
    def type_names(self):
        return self.type.type_names

    @property
    def extended_attributes(self):
        return self._extended_attributes if (self._extended_attributes) else {}

    def _str(self):
        return (str(self._extended_attributes) if (self._extended_attributes) else '') + str(self.type) + (self.suffix._str() if (self.suffix) else '')

    def _markup(self, generator):
        if (self._extended_attributes):
            self._extended_attributes.markup(generator)
        self.type.markup(generator)
        generator.add_text(self.suffix)
        return self

    def __repr__(self):
        return ('[TypeWithExtendedAttributes: ' + (repr(self._extended_attributes) if (self._extended_attributes) else '')
                + repr(self.type) + (repr(self.suffix) if (self.suffix) else '') + ']')


class IgnoreInOut(Production):
    """
    Consume an 'in' or 'out' token to ignore for backwards compat.

    Syntax:
    "in" | "out"
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        if (token and token.is_identifier() and (('in' == token.text) or ('out' == token.text))):
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.text = tokens.next().text
        self._did_parse(tokens)
        tokens.did_ignore(self.text)

    def _str(self):
        return self.text


class Ignore(Production):
    """
    Consume deprecated syntax for backwards compat.

    Syntax:
    "inherits" "getter" | "getraises" "(" ... ")" | "setraises" "(" ... ")" | "raises" "(" ... ")"
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        if (token and token.is_identifier() and ('inherits' == token.text)):
            token = tokens.peek()
            return tokens.pop_position(token and token.is_symbol('getter'))
        if (token and token.is_identifier()
                and (('getraises' == token.text) or ('setraises' == token.text) or ('raises' == token.text))):
            token = tokens.peek()
            if (token and token.is_symbol('(')):
                return tokens.pop_position(tokens.peek_symbol(')'))
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.tokens = []
        token = tokens.next()
        self.tokens.append(token)
        if (token and token.is_identifier() and ('inherits' == token.text)):
            space = tokens.whitespace()
            if (space):
                self.tokens.append(space)
            self.tokens.append(tokens.next())   # "getter"
        else:
            space = tokens.whitespace()
            if (space):
                self.tokens.append(space)
            self.tokens.append(tokens.next())    # "("
            self.tokens += tokens.seek_symbol(')')
        self._did_parse(tokens)
        tokens.did_ignore(self.tokens)

    def _str(self):
        return ''.join([str(token) for token in self.tokens])


class IgnoreMultipleInheritance(Production):
    """
    Consume deprecated multiple inheritance syntax for backwards compat.

    Syntax:
    [, Identifier]...
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, ',')):
            if (TypeIdentifier.peek(tokens)):
                IgnoreMultipleInheritance.peek(tokens)
                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens, continuation = False):
        Production.__init__(self, tokens)
        self._comma = Symbol(tokens, ',')
        self._inherit = TypeIdentifier(tokens)
        self.next = IgnoreMultipleInheritance(tokens, True) if (IgnoreMultipleInheritance.peek(tokens)) else None
        self._did_parse(tokens)
        if (not continuation):
            tokens.did_ignore(self)

    def _str(self):
        return str(self._comma) + str(self._inherit) + (str(self.next) if (self.next) else '')

    @property
    def inherit(self):
        return self._inherit.name

    def _markup(self, generator):
        generator.add_text(self._comma)
        self._inherit.markup(generator)
        if (self.next):
            self.next.markup(generator)
        return self


class Inheritance(Production):
    """
    Inheritance production.

    Syntax:
    ":" Identifier [IgnoreMultipleInheritance]
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, ':')):
            if (TypeIdentifier.peek(tokens)):
                IgnoreMultipleInheritance.peek(tokens)
                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._colon = Symbol(tokens, ':')
        self._base = TypeIdentifier(tokens)
        self._ignore = IgnoreMultipleInheritance(tokens) if (IgnoreMultipleInheritance.peek(tokens)) else None
        self._did_parse(tokens)

    @property
    def base(self):
        return self._base.name

    def _str(self):
        return str(self._colon) + str(self._base) + (str(self._ignore) if (self._ignore) else '')

    def _markup(self, generator):
        generator.add_text(self._colon)
        self._base.markup(generator)
        if (self._ignore):
            self._ignore.markup(generator)
        return self

    def __repr__(self):
        return '[Inheritance: ' + repr(self._base) + ']'


class Default(Production):
    """
    Default value production.

    Syntax:
    "=" ConstValue | "=" String | "=" "[" "]" | "=" "{" "}"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, '=')):
            if (ConstValue.peek(tokens)):
                return tokens.pop_position(True)
            if (Symbol.peek(tokens, '[')):
                return tokens.pop_position(Symbol.peek(tokens, ']'))
            if (Symbol.peek(tokens, '{')):
                return tokens.pop_position(Symbol.peek(tokens, '}'))
            token = tokens.peek()
            return tokens.pop_position(token and token.is_string())
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._equals = Symbol(tokens, '=')
        self._open = None
        self._close = None
        self._value = None
        token = tokens.sneak_peek()
        if (token.is_string()):
            self._value = String(tokens)
        elif (token.is_symbol('[')):
            self._open = Symbol(tokens, '[')
            self._close = Symbol(tokens, ']', False)
        elif (token.is_symbol('{')):
            self._open = Symbol(tokens, '{')
            self._close = Symbol(tokens, '}', False)
        else:
            self._value = ConstValue(tokens)
        self._did_parse(tokens)

    @property
    def value(self) -> str:
        return str(self._value) if (self._value) else (self._open._str() + self._close._str())

    def _str(self) -> str:
        return str(self._equals) + (str(self._value) if (self._value) else str(self._open) + str(self._close))

    def _markup(self, generator):
        self._equals.markup(generator)
        if (self._value):
            return self._value._markup(generator)
        self._open.markup(generator)
        self._close.markup(generator)
        return self

    def __repr__(self):
        return '[Default: ' + (repr(self.value) if (self.value) else str(self._open) + str(self._close)) + ']'


class ArgumentName(Production):
    """
    Argument name production.

    Syntax:
    Identifier | ArgumentNameKeyword
    """

    ARGUMENT_NAME_KEYWORDS = frozenset(['async', 'attribute', 'callback', 'const', 'constructor',
                                        'deleter', 'dictionary', 'enum', 'getter', 'includes',
                                        'inherit', 'interface', 'iterable', 'maplike', 'namespace',
                                        'partial', 'required', 'setlike', 'setter', 'static',
                                        'stringifier', 'typedef', 'unrestricted'])

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and (token.is_identifier() or (token.is_symbol() and (token.text in cls.ARGUMENT_NAME_KEYWORDS))))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._name = Identifier(tokens)
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        return str(self._name)

    def _markup(self, generator):
        self._name.markup(generator)
        return self

    def __repr__(self):
        return '[ArgumentName: ' + repr(self._name) + ']'


class ArgumentList(Production):
    """
    Argument list production.

    Syntax:
    Argument ["," Argument]...
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (constructs.Argument.peek(tokens)):
            token = tokens.push_position()
            if (token and token.is_symbol(',')):
                return tokens.pop_position(tokens.pop_position(ArgumentList.peek(tokens)))
            tokens.pop_position(False)
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Production.__init__(self, tokens)
        self.arguments = []
        self._commas = []
        self.arguments.append(constructs.Argument(tokens, parent))
        token = tokens.sneak_peek()
        while (token and token.is_symbol(',')):
            self._commas.append(Symbol(tokens, ','))
            argument = constructs.Argument(tokens, parent)
            if (len(self.arguments)):
                if (self.arguments[-1].variadic):
                    tokens.error('Argument "', argument.name, '" not allowed to follow variadic argument "', self.arguments[-1].name, '"')
                elif ((not self.arguments[-1].required) and argument.required):
                    tokens.error('Required argument "', argument.name, '" cannot follow optional argument "', self.arguments[-1].name, '"')
            self.arguments.append(argument)
            token = tokens.sneak_peek()
        self._did_parse(tokens)
        if (parent):
            for index in range(0, len(self.arguments)):
                argument = self.arguments[index]
                if (argument.required):
                    for type_name in argument.type.type_names:
                        type = parent.parser.get_type(type_name)
                        if (type and ('dictionary' == type.idl_type) and (not type.required)):    # must be optional unless followed by required argument
                            for index2 in range(index + 1, len(self.arguments)):
                                if (self.arguments[index2].required):
                                    break
                            else:
                                tokens.error('Dictionary argument "', argument.name, '" without required members must be marked optional')

    @property
    def name(self):
        return self.arguments[0].name

    @property   # get all possible variants of argument names
    def argument_names(self):
        if (self.arguments):
            args = [argument for argument in self.arguments]
            names = []
            name = ', '.join([('...' + argument.name) if (argument.variadic) else argument.name for argument in args])
            names.append(name)
            while (args and (args[-1].optional)):
                args.pop()
                names.append(', '.join([argument.name for argument in args]))
            return names
        return ['']

    def matches_names(self, argument_names):
        for name, argument in itertools.zip_longest(argument_names, self.arguments, fillvalue=None):
            if (name):
                if ((argument is None) or (argument.name != name)):
                    return False
            else:
                if (argument and argument.required):
                    return False
        return True

    def __len__(self):
        return len(self.arguments)

    def keys(self):
        return [argument.name for argument in self.arguments]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for argument in self.arguments:
                if (argument.name == key):
                    return argument
            return None
        return self.arguments[key]

    def __iter__(self):
        return iter(self.arguments)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for argument in self.arguments:
                if (argument.name == key):
                    return True
            return False
        return (key in self.arguments)

    def _str(self):
        return ''.join([str(argument) + str(comma) for argument, comma in itertools.zip_longest(self.arguments, self._commas, fillvalue = '')])

    def _markup(self, generator):
        for argument, comma in itertools.zip_longest(self.arguments, self._commas, fillvalue = ''):
            argument.markup(generator)
            generator.add_text(comma)
        return self

    def __repr__(self):
        return ' '.join([repr(argument) for argument in self.arguments])


class ReturnType(Production):
    """
    Return type production.

    Syntax:
    Type | "void"
    """

    @classmethod
    def peek(cls, tokens):
        if (Type.peek(tokens)):
            return True
        token = tokens.push_position()
        return tokens.pop_position(token and token.is_symbol('void'))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        token = tokens.sneak_peek()
        if (token.is_symbol('void')):
            self.type = Symbol(tokens, 'void', False)
        else:
            self.type = Type(tokens)
        self._did_parse(tokens)

    def _str(self):
        return str(self.type)

    def _markup(self, generator):
        if (isinstance(self.type, Symbol)):
            self.type._markup(generator)
        else:
            generator.add_type(self.type)
        return self

    def __repr__(self):
        return repr(self.type)


class Special(Production):
    """
    Special production.

    Syntax:
    "getter" | "setter" | "creator" | "deleter" | "legacycaller"
    """

    SPECIAL_SYMBOLS = frozenset(['getter', 'setter', 'creator', 'deleter', 'legacycaller'])
    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and token.is_symbol() and (token.text in cls.SPECIAL_SYMBOLS))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.name = tokens.next().text
        self._did_parse(tokens)

    def _str(self):
        return self.name

    def _markup(self, generator):
        generator.add_keyword(self.name)
        return self

    def __repr__(self):
        return '[Special: ' + self.name + ']'


class AttributeName(Production):
    """
    Atttribute name production.

    Syntax:
    Identifier | AttributeNameKeyword
    """

    ATTRIBUTE_NAME_KEYWORDS = frozenset(['async', 'required'])

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and (token.is_identifier() or (token.is_symbol() and (token.text in cls.ATTRIBUTE_NAME_KEYWORDS))))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._name = Identifier(tokens)
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        return str(self._name)

    def _markup(self, generator):
        self._name.markup(generator)
        return self

    def __repr__(self):
        return '[OperationName: ' + repr(self._name) + ']'


class AttributeRest(Production):
    """
    Atttribute rest production.

    Syntax:
    ["readonly"] "attribute" TypeWithExtendedAttributes AttributeName [Ignore] ";"
    """

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        if (token and token.is_symbol('readonly')):
            token = tokens.peek()
        if (token and token.is_symbol('attribute')):
            if (TypeWithExtendedAttributes.peek(tokens)):
                return tokens.pop_position(AttributeName.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self.readonly = Symbol(tokens, 'readonly') if (Symbol.peek(tokens, 'readonly')) else None
        self._attribute = Symbol(tokens, 'attribute')
        self.type = TypeWithExtendedAttributes(tokens)
        self._name = AttributeName(tokens)
        self._ignore = Ignore(tokens) if (Ignore.peek(tokens)) else None
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        output = str(self.readonly) if (self.readonly) else ''
        output += str(self._attribute) + str(self.type)
        output += str(self._name)
        return output + (str(self._ignore) if (self._ignore) else '')

    def _markup(self, generator):
        if (self.readonly):
            self.readonly.markup(generator)
        self._attribute.markup(generator)
        generator.add_type(self.type)
        self._name.markup(generator)
        if (self._ignore):
            self._ignore.markup(generator)
        return self

    def __repr__(self):
        output = '[AttributeRest: '
        output += '[readonly] ' if (self.readonly) else ''
        output += repr(self.type)
        output += ' [name: ' + self.name + ']'
        return output + ']'


class ChildProduction(Production):
    """Base class for productions that have parents."""

    def __init__(self, tokens, parent):
        Production.__init__(self, tokens)
        self.parent = parent

    @property
    def full_name(self):
        return self.parent.full_name + '/' + self.normal_name if (self.parent) else self.normal_name

    @property
    def method_name(self):
        return None

    @property
    def method_names(self):
        return []

    @property
    def normal_name(self):
        return self.method_name if (self.method_name) else self.name

    @property
    def parser(self):
        return self.parent.parser


class MixinAttribute(ChildProduction):
    """
    Mixin atttribute production.

    Syntax:
    AttributeRest
    """

    @classmethod
    def peek(cls, tokens):
        return AttributeRest.peek(tokens)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.attribute = AttributeRest(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'attribute'

    @property
    def stringifier(self):
        return False

    @property
    def name(self):
        return self.attribute.name

    @property
    def arguments(self):
        return None

    def _str(self):
        return str(self.attribute)

    def _markup(self, generator):
        return self.attribute._markup(generator)

    def __repr__(self):
        output = '[Attribute: '
        return output + repr(self.attribute) + ']'


class Attribute(ChildProduction):
    """
    Atttribute production.

    Syntax:
    ["inherit"] AttributeRest
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Symbol.peek(tokens, 'inherit')
        return tokens.pop_position(AttributeRest.peek(tokens))

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.inherit = Symbol(tokens, 'inherit') if (Symbol.peek(tokens, 'inherit')) else None
        self.attribute = AttributeRest(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'attribute'

    @property
    def stringifier(self):
        return False

    @property
    def name(self):
        return self.attribute.name

    @property
    def arguments(self):
        return None

    def _str(self):
        output = str(self.inherit) if (self.inherit) else ''
        return output + str(self.attribute)

    def _markup(self, generator):
        if (self.inherit):
            self.inherit.markup(generator)
        return self.attribute._markup(generator)

    def __repr__(self):
        output = '[Attribute: '
        output += '[inherit] ' if (self.inherit) else ''
        return output + repr(self.attribute) + ']'


class OperationName(Production):
    """
    Operation name production.

    Syntax:
    Identifier | OperationNameKeyword
    """

    OPERATION_NAME_KEYWORDS = frozenset(['includes'])

    @classmethod
    def peek(cls, tokens):
        token = tokens.push_position()
        return tokens.pop_position(token and (token.is_identifier() or (token.is_symbol() and (token.text in cls.OPERATION_NAME_KEYWORDS))))

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._name = Identifier(tokens)
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        return str(self._name)

    def _markup(self, generator):
        self._name.markup(generator)
        return self

    def __repr__(self):
        return '[OperationName: ' + repr(self._name) + ']'


class OperationRest(ChildProduction):
    """
    Operation rest production.

    Syntax:
    [OperationName] "(" [ArgumentList] ")" [Ignore] ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        OperationName.peek(tokens)
        token = tokens.peek()
        if (token and token.is_symbol('(')):
            ArgumentList.peek(tokens)
            token = tokens.peek()
            return tokens.pop_position(token and token.is_symbol(')'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._name = OperationName(tokens) if (OperationName.peek(tokens)) else None
        self._open_paren = Symbol(tokens, '(')
        self.arguments = ArgumentList(tokens, parent) if (ArgumentList.peek(tokens)) else None
        self._close_paren = Symbol(tokens, ')')
        self._ignore = Ignore(tokens) if (Ignore.peek(tokens)) else None
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'method'

    @property
    def name(self):
        return self._name.name if (self._name) else None

    @property
    def argument_names(self):
        return self.arguments.argument_names if (self.arguments) else ['']

    def _str(self):
        output = str(self._name) if (self._name) else ''
        output += str(self._open_paren) + (str(self.arguments) if (self.arguments) else '') + str(self._close_paren)
        return output + (str(self._ignore) if (self._ignore) else '')

    def _markup(self, generator):
        if (self._name):
            self._name.markup(generator)
        generator.add_text(self._open_paren)
        if (self.arguments):
            self.arguments.markup(generator)
        generator.add_text(self._close_paren)
        if (self._ignore):
            self._ignore.markup(generator)
        return self

    def __repr__(self):
        output = '[OperationRest: '
        output += ('[name: ' + repr(self._name) + '] ') if (self._name) else ''
        return output + '[ArgumentList: ' + (repr(self.arguments) if (self.arguments) else '') + ']]'


class Iterable(ChildProduction):
    """
    Iterable production.

    Syntax:
    "iterable" "<" TypeWithExtendedAttributes ["," TypeWithExtendedAttributes] ">" ";" | "legacyiterable" "<" Type ">" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'iterable')):
            if (Symbol.peek(tokens, '<')):
                if (TypeWithExtendedAttributes.peek(tokens)):
                    if (Symbol.peek(tokens, ',')):
                        if (TypeWithExtendedAttributes.peek(tokens)):
                            token = tokens.peek()
                            return tokens.pop_position(token and token.is_symbol('>'))
                    token = tokens.peek()
                    return tokens.pop_position(token and token.is_symbol('>'))
        elif (Symbol.peek(tokens, 'legacyiterable')):
            if (Symbol.peek(tokens, '<')):
                if (Type.peek(tokens)):
                    token = tokens.peek()
                    return tokens.pop_position(token and token.is_symbol('>'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._iterable = Symbol(tokens)
        self._open_type = Symbol(tokens, '<')
        self.type = TypeWithExtendedAttributes(tokens)
        if (Symbol.peek(tokens, ',')):
            self.key_type = self.type
            self.type = None
            self._comma = Symbol(tokens)
            self.value_type = TypeWithExtendedAttributes(tokens)
        else:
            self.key_type = None
            self.value_type = None
        self._close_type = Symbol(tokens, '>')
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'iterable'

    @property
    def name(self):
        return '__iterable__'

    @property
    def arguments(self):
        return None

    def _str(self):
        output = str(self._iterable) + str(self._open_type)
        if (self.type):
            output += str(self.type)
        else:
            output += str(self.key_type) + str(self._comma) + str(self.value_type)
        return output + str(self._close_type)

    def _markup(self, generator):
        self._iterable.markup(generator)
        generator.add_text(self._open_type)
        if (self.type):
            generator.add_type(self.type)
        else:
            generator.add_type(self.key_type)
            generator.add_text(self._comma)
            generator.add_type(self.value_type)
        generator.add_text(self._close_type)
        return self

    def __repr__(self):
        output = '[Iterable: '
        if (self.type):
            output += repr(self.type)
        else:
            output += repr(self.key_type) + ' ' + repr(self.value_type)
        return output + ']'


class AsyncIterable(ChildProduction):
    """
    Async iterable production.

    Syntax:
    "async" "iterable" "<" TypeWithExtendedAttributes "," TypeWithExtendedAttributes ">" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'async')):
            if (Symbol.peek(tokens, 'iterable')):
                if (Symbol.peek(tokens, '<')):
                    if (TypeWithExtendedAttributes.peek(tokens)):
                        if (Symbol.peek(tokens, ',')):
                            if (TypeWithExtendedAttributes.peek(tokens)):
                                token = tokens.peek()
                                return tokens.pop_position(token and token.is_symbol('>'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._async = Symbol(tokens)
        self._iterable = Symbol(tokens)
        self._open_type = Symbol(tokens, '<')
        self.key_type = TypeWithExtendedAttributes(tokens)
        self._comma = Symbol(tokens)
        self.value_type = TypeWithExtendedAttributes(tokens)
        self._close_type = Symbol(tokens, '>')
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'async-iterable'

    @property
    def name(self):
        return '__async_iterable__'

    @property
    def arguments(self):
        return None

    def _str(self):
        output = str(self._async) + str(self._iterable) + str(self._open_type)
        output += str(self.key_type) + str(self._comma) + str(self.value_type)
        return output + str(self._close_type)

    def _markup(self, generator):
        self._async.markup(generator)
        self._iterable.markup(generator)
        generator.add_text(self._open_type)
        generator.add_type(self.key_type)
        generator.add_text(self._comma)
        generator.add_type(self.value_type)
        generator.add_text(self._close_type)
        return self

    def __repr__(self):
        output = '[AsyncIterable: '
        output += repr(self.key_type) + ' ' + repr(self.value_type)
        return output + ']'


class Maplike(ChildProduction):
    """
    Maplike production.

    Syntax:
    ["readonly"] "maplike" "<" TypeWithExtendedAttributes "," TypeWithExtendedAttributes ">" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Symbol.peek(tokens, 'readonly')
        if (Symbol.peek(tokens, 'maplike')):
            if (Symbol.peek(tokens, '<')):
                if (TypeWithExtendedAttributes.peek(tokens)):
                    if (Symbol.peek(tokens, ',')):
                        if (TypeWithExtendedAttributes.peek(tokens)):
                            return tokens.pop_position(Symbol.peek(tokens, '>'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.readonly = Symbol(tokens, 'readonly') if (Symbol.peek(tokens, 'readonly')) else None
        self._maplike = Symbol(tokens, 'maplike')
        self._open_type = Symbol(tokens, '<')
        self.key_type = TypeWithExtendedAttributes(tokens)
        self._comma = Symbol(tokens, ',')
        self.value_type = TypeWithExtendedAttributes(tokens)
        self._close_type = Symbol(tokens, '>')
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'maplike'

    @property
    def name(self):
        return '__maplike__'

    @property
    def arguments(self):
        return None

    def _str(self):
        output = str(self.readonly) if (self.readonly) else ''
        output += str(self._maplike) + str(self._open_type) + str(self.key_type) + str(self._comma)
        return output + str(self.value_type) + str(self._close_type)

    def _markup(self, generator):
        if (self.readonly):
            self.readonly.markup(generator)
        self._maplike.markup(generator)
        generator.add_text(self._open_type)
        generator.add_type(self.key_type)
        generator.add_text(self._comma)
        generator.add_type(self.value_type)
        generator.add_text(self._close_type)
        return self

    def __repr__(self):
        output = '[Maplike: ' + '[readonly] ' if (self.readonly) else ''
        output += repr(self.key_type) + ' ' + repr(self.value_type)
        return output + ']'


class Setlike(ChildProduction):
    """
    Setlike production.

    Syntax:
    ["readonly"] "setlike" "<" TypeWithExtendedAttributes ">" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Symbol.peek(tokens, 'readonly')
        if (Symbol.peek(tokens, 'setlike')):
            if (Symbol.peek(tokens, '<')):
                if (TypeWithExtendedAttributes.peek(tokens)):
                    return tokens.pop_position(Symbol.peek(tokens, '>'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.readonly = Symbol(tokens, 'readonly') if (Symbol.peek(tokens, 'readonly')) else None
        self._setlike = Symbol(tokens, 'setlike')
        self._open_type = Symbol(tokens, '<')
        self.type = TypeWithExtendedAttributes(tokens)
        self._close_type = Symbol(tokens, '>')
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'setlike'

    @property
    def name(self):
        return '__setlike__'

    @property
    def arguments(self):
        return None

    def _str(self):
        output = str(self.readonly) if (self.readonly) else ''
        return output + str(self._setlike) + str(self._open_type) + str(self.type) + str(self._close_type)

    def _markup(self, generator):
        if (self.readonly):
            self.readonly.markup(generator)
        self._setlike.markup(generator)
        generator.add_text(self._open_type)
        generator.add_type(self.type)
        generator.add_text(self._close_type)
        return self

    def __repr__(self):
        output = '[Setlike: ' + ('[readonly] ' if (self.readonly) else '')
        return output + repr(self.type) + ']'


class SpecialOperation(ChildProduction):
    """
    Special operation production.

    Syntax:
    Special [Special]... ReturnType OperationRest
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Special.peek(tokens)):
            while (Special.peek(tokens)):
                pass
            if (ReturnType.peek(tokens)):
                return tokens.pop_position(OperationRest.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.specials = []
        while (Special.peek(tokens)):
            self.specials.append(Special(tokens))
        self.return_type = ReturnType(tokens)
        self.operation = OperationRest(tokens, self)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'method'

    @property
    def name(self):
        return self.operation.name if (self.operation.name) else ('__' + self.specials[0].name + '__')

    @property
    def arguments(self):
        return self.operation.arguments

    @property
    def method_name(self):
        name = self.name + '(' if (self.name) else '('
        if (self.arguments):
            name += self.arguments.argument_names[0]
        return name + ')'

    @property
    def method_names(self):
        if (self.arguments):
            return [_name(self) + '(' + argument_name + ')' for argument_name in self.arguments.argument_names]
        return [self.method_name]

    def _str(self):
        output = ''.join([str(special) for special in self.specials])
        return output + str(self.return_type) + str(self.operation)

    def _markup(self, generator):
        for special in self.specials:
            special.markup(generator)
        self.return_type.markup(generator)
        return self.operation._markup(generator)

    def __repr__(self):
        output = '[SpecialOperation: ' + ' '.join([repr(special) for special in self.specials])
        return output + ' ' + repr(self.return_type) + ' ' + repr(self.operation) + ']'


class Operation(ChildProduction):
    """
    Operation production.

    Syntax:
    ReturnType OperationRest
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (ReturnType.peek(tokens)):
            return tokens.pop_position(OperationRest.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self.return_type = ReturnType(tokens)
        self.operation = OperationRest(tokens, self)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'method'

    @property
    def name(self):
        return self.operation.name

    @property
    def arguments(self):
        return self.operation.arguments

    @property
    def method_name(self):
        name = self.name + '(' if (self.name) else '('
        if (self.arguments):
            name += self.arguments.argument_names[0]
        return name + ')'

    @property
    def method_names(self):
        if (self.arguments):
            return [_name(self) + '(' + argument_name + ')' for argument_name in self.arguments.argument_names]
        return [self.method_name]

    def _str(self):
        return str(self.return_type) + str(self.operation)

    def _markup(self, generator):
        self.return_type.markup(generator)
        return self.operation._markup(generator)

    def __repr__(self):
        return '[Operation: ' + repr(self.return_type) + ' ' + repr(self.operation) + ']'


class Stringifier(ChildProduction):
    """
    Stringifier production.

    Syntax:
    "stringifier" AttributeRest | "stringifier" ReturnType OperationRest | "stringifier" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'stringifier')):
            if (ReturnType.peek(tokens)):
                return tokens.pop_position(OperationRest.peek(tokens))
            AttributeRest.peek(tokens)
            return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._stringifier = Symbol(tokens, 'stringifier')
        self.attribute = None
        self.return_type = None
        self.operation = None
        if (ReturnType.peek(tokens)):
            self.return_type = ReturnType(tokens)
            self.operation = OperationRest(tokens, self)
        elif (AttributeRest.peek(tokens)):
            self.attribute = AttributeRest(tokens)
        else:
            self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'attribute' if (self.attribute) else 'stringifier'

    @property
    def stringifier(self):
        return True

    @property
    def name(self):
        if (self.operation):
            return self.operation.name if (self.operation.name) else '__stringifier__'
        return self.attribute.name if (self.attribute and self.attribute.name) else '__stringifier__'

    @property
    def arguments(self):
        return self.operation.arguments if (self.operation) else None

    @property
    def method_name(self):
        if (self.operation):
            name = self.name + '(' if (self.name) else '('
            if (self.arguments):
                name += self.arguments.argument_names[0]
            return name + ')'
        return None

    @property
    def method_names(self):
        if (self.operation):
            if (self.arguments):
                return [_name(self) + '(' + argument_name + ')' for argument_name in self.arguments.argument_names]
            return [self.method_name]
        return []

    def _str(self):
        output = str(self._stringifier)
        output += (str(self.return_type) + str(self.operation)) if (self.operation) else ''
        return output + (str(self.attribute) if (self.attribute) else '')

    def _markup(self, generator):
        self._stringifier.markup(generator)
        if (self.operation):
            self.return_type.markup(generator)
            return self.operation._markup(generator)
        if (self.attribute):
            return self.attribute._markup(generator)
        return self

    def __repr__(self):
        output = '[Stringifier: '
        if (self.operation):
            output += repr(self.return_type) + ' ' + repr(self.operation)
        else:
            output += repr(self.attribute) if (self.attribute) else ''
        return output + ']'


class Identifiers(Production):
    """
    Identifiers production.

    Syntax:
    "," Identifier ["," Identifier]...
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, ',')):
            if (Identifier.peek(tokens)):
                Identifiers.peek(tokens)
                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._comma = Symbol(tokens, ',')
        self._name = Identifier(tokens)
        self.next = Identifiers(tokens) if (Identifiers.peek(tokens)) else None
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        output = str(self._comma) + str(self._name)
        return output + (str(self.next) if (self.next) else '')

    def __repr__(self):
        return ' ' + repr(self._name) + (repr(self.next) if (self.next) else '')


class TypeIdentifiers(Production):
    """
    Type identifiers production.

    Syntax:
    "," Identifier ["," Identifier]...
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, ',')):
            if (TypeIdentifier.peek(tokens)):
                TypeIdentifiers.peek(tokens)
                return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens):
        Production.__init__(self, tokens)
        self._comma = Symbol(tokens, ',')
        self._name = TypeIdentifier(tokens)
        self.next = TypeIdentifiers(tokens) if (TypeIdentifiers.peek(tokens)) else None
        self._did_parse(tokens)

    @property
    def name(self):
        return self._name.name

    def _str(self):
        output = str(self._comma) + str(self._name)
        return output + (str(self.next) if (self.next) else '')

    def __repr__(self):
        return ' ' + repr(self._name) + (repr(self.next) if (self.next) else '')


class StaticMember(ChildProduction):
    """
    Static member production.

    Syntax:
    "static" AttributeRest | "static" ReturnType OperationRest
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'static')):
            if (AttributeRest.peek(tokens)):
                return tokens.pop_position(True)
            if (ReturnType.peek(tokens)):
                return tokens.pop_position(OperationRest.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._static = Symbol(tokens, 'static')
        if (AttributeRest.peek(tokens)):
            self.attribute = AttributeRest(tokens)
            self.return_type = None
            self.operation = None
        else:
            self.attribute = None
            self.return_type = ReturnType(tokens)
            self.operation = OperationRest(tokens, self)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'method' if (self.operation) else 'attribute'

    @property
    def stringifier(self):
        return False

    @property
    def name(self):
        return self.operation.name if (self.operation) else self.attribute.name

    @property
    def arguments(self):
        return self.operation.arguments if (self.operation) else None

    @property
    def method_name(self):
        if (self.operation):
            name = self.name + '(' if (self.name) else '('
            if (self.arguments):
                name += self.arguments.argument_names[0]
            return name + ')'
        return None

    @property
    def method_names(self):
        if (self.operation):
            if (self.arguments):
                return [_name(self) + '(' + argument_name + ')' for argument_name in self.arguments.argument_names]
            return [self.method_name]
        return []

    def _str(self):
        output = str(self._static)
        if (self.operation):
            return output + str(self.return_type) + str(self.operation)
        return output + str(self.attribute)

    def _markup(self, generator):
        self._static.markup(generator)
        if (self.operation):
            self.return_type.markup(generator)
            return self.operation._markup(generator)
        return self.attribute._markup(generator)

    def __repr__(self):
        output = '[StaticMember: '
        if (self.operation):
            return output + repr(self.return_type) + ' ' + repr(self.operation) + ']'
        return output + repr(self.attribute) + ']'


class Constructor(ChildProduction):
    """
    Constructor production.

    Syntax:
    "constructor" "(" ArgumentList ")" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'constructor')):
            if (Symbol.peek(tokens, '(')):
                ArgumentList.peek(tokens)
                token = tokens.peek()
                return tokens.pop_position(token and token.is_symbol(')'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._constructor = Identifier(tokens)  # treat 'constructor' as a name
        self._open_paren = Symbol(tokens, '(')
        self.arguments = ArgumentList(tokens, self) if (ArgumentList.peek(tokens)) else None
        self._close_paren = Symbol(tokens, ')')
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'method'

    @property
    def name(self):
        return self._constructor.name

    @property
    def stringifier(self):
        return False

    @property
    def argument_names(self):
        return self.arguments.argument_names if (self.arguments) else ['']

    @property
    def method_name(self):
        name = 'constructor('
        if (self.arguments):
            name += self.arguments.argument_names[0]
        return name + ')'

    @property
    def method_names(self):
        if (self.arguments):
            return ['constructor(' + argument_name + ')' for argument_name in self.arguments.argument_names]
        return [self.method_name]

    def _str(self):
        output = self.name if (self.name) else ''
        return output + str(self._open_paren) + (str(self.arguments) if (self.arguments) else '') + str(self._close_paren)

    def _markup(self, generator):
        if (self._constructor):
            self._constructor.markup(generator)
        generator.add_text(self._open_paren)
        if (self.arguments):
            self.arguments.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        output = '[Constructor: '
        return output + '[ArgumentList: ' + (repr(self.arguments) if (self.arguments) else '') + ']]'


class ExtendedAttributeList(ChildProduction):
    """
    Extended attribute list production.

    Syntax:
    "[" ExtendedAttribute ["," ExtendedAttribute]... "]"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Symbol.peek(tokens, '[')):
            return tokens.pop_position(tokens.peek_symbol(']'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        ChildProduction.__init__(self, tokens, parent)
        self._open_bracket = Symbol(tokens, '[')
        self.attributes = []
        self._commas = []
        while (tokens.has_tokens()):
            self.attributes.append(constructs.ExtendedAttribute(tokens, parent))
            token = tokens.sneak_peek()
            if ((not token) or token.is_symbol(']')):
                break
            if (token.is_symbol(',')):
                self._commas.append(Symbol(tokens, ','))
                continue
        self._close_bracket = Symbol(tokens, ']')
        self._did_parse(tokens)

    def __len__(self):
        return len(self.attributes)

    def keys(self):
        return [attribute.name for attribute in self.attributes]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for attribute in self.attributes:
                if (key == attribute.name):
                    return attribute
            return None
        return self.attributes[key]

    def __iter__(self):
        return iter(self.attributes)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for attribute in self.attributes:
                if (key == attribute.name):
                    return True
            return False
        return (key in self.attributes)

    def _str(self):
        output = str(self._open_bracket)
        output += ''.join([str(attribute) + str(comma) for attribute, comma in itertools.zip_longest(self.attributes, self._commas, fillvalue = '')])
        return output + str(self._close_bracket)

    def _markup(self, generator):
        generator.add_text(self._open_bracket)
        for attribute, comma in itertools.zip_longest(self.attributes, self._commas, fillvalue = ''):
            attribute.markup(generator)
            generator.add_text(comma)
        generator.add_text(self._close_bracket)
        return self

    def __repr__(self):
        return '[ExtendedAttributes: ' + ' '.join([repr(attribute) for attribute in self.attributes]) + '] '
