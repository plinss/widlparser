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
"""High-level WebIDL constructs."""

from . import markup
from .productions import (ArgumentList, ArgumentName, AsyncIterable, Attribute, ChildProduction, ConstType, ConstValue, Constructor, Default, EnumValueList,
                          ExtendedAttributeList, Identifier, IgnoreInOut, Inheritance, Iterable,
                          Maplike, MixinAttribute, Operation, ReturnType, Setlike, SpecialOperation, StaticMember, Stringifier, Symbol,
                          Type, TypeIdentifier, TypeIdentifiers, TypeWithExtendedAttributes)


class Construct(ChildProduction):
    """Base class for high-level language constructs."""

    @classmethod
    def peek(cls, tokens):
        """Check if construct is next in token stream."""
        return ExtendedAttributeList.peek(tokens)

    def __init__(self, tokens, parent, parse_extended_attributes = True, parser = None):
        ChildProduction.__init__(self, tokens, parent)
        self._parser = parser
        self._extended_attributes = self._parse_extended_attributes(tokens, self) if (parse_extended_attributes) else None

    def _parse_extended_attributes(self, tokens, parent):
        return ExtendedAttributeList(tokens, parent) if (ExtendedAttributeList.peek(tokens)) else None

    @property
    def idl_type(self):
        """Get construct type."""
        assert(False)   # subclasses must override
        return None

    @property
    def constructors(self):
        """Get constructors."""
        return [attribute for attribute in self._extended_attributes if ('constructor' == attribute.idl_type)] if (self._extended_attributes) else []

    @property
    def parser(self):
        """Get parser."""
        return self._parser if (self._parser is not None) else self.parent.parser

    @property
    def extended_attributes(self):
        """Get extended attributes."""
        return self._extended_attributes if (self._extended_attributes) else {}

    def __bool__(self):
        """Presence detection."""
        return True

    def __len__(self):
        """Number of children."""
        return 0

    def keys(self):
        """Names of children."""
        return []

    def __getitem__(self, key):
        """Access child by index."""
        return None

    def __iter__(self):
        """Iterate over children."""
        return iter(())

    def __contains__(self, key):
        """Test if child is present."""
        return False

    def find_member(self, name):
        """Search for child member of a given name."""
        return None

    def find_members(self, name):
        """Search for all child members of a given name."""
        return []

    def find_method(self, name, argument_names=None):
        """Search for a method of a given name."""
        return None

    def find_methods(self, name, argument_names=None):
        """Search for all methods of a given name."""
        return []

    def find_argument(self, name, search_members = True):
        """Search for an argument of a given name."""
        return None

    def find_arguments(self, name, search_members = True):
        """Search for all argument of a given name."""
        return []

    @property
    def complexity_factor(self):
        """Get complexity factor."""
        return 1

    def _str(self):
        """Convert to string."""
        return str(self._extended_attributes) if (self._extended_attributes) else ''

    def __repr__(self):
        """Debug info."""
        return repr(self._extended_attributes) if (self._extended_attributes) else ''

    def markup(self, generator):
        """Generate marked up version of self."""
        if (not generator):
            return str(self)

        if (isinstance(generator, markup.MarkupGenerator)):
            marker = None
            generator.add_text(self._leading_space)
        else:
            marker = generator
            generator = None

        my_generator = markup.MarkupGenerator(self)
        if (self._extended_attributes):
            self._extended_attributes.markup(my_generator)
        target = self._markup(my_generator)
        if (target._tail):
            my_generator.add_text(''.join([str(token) for token in target._tail]))
        my_generator.add_text(str(target._semicolon))

        if (generator):
            generator.add_generator(my_generator)
            if (self != target):
                generator.add_text(target._trailing_space)
            generator.add_text(self._trailing_space)
            return self
        return my_generator.markup(marker)


class Const(Construct):
    """
    WebIDL "const".

    Syntax:
    "const" ConstType Identifier "=" ConstValue ";"
    """

    @classmethod
    def peek(cls, tokens):
        """Check if Const is next in token stream."""
        tokens.push_position(False)
        if (Symbol.peek(tokens, 'const')):
            if (ConstType.peek(tokens)):
                if (Identifier.peek(tokens)):
                    if (Symbol.peek(tokens, '=')):
                        return tokens.pop_position(ConstValue.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, False, parser = parser)
        self._const = Symbol(tokens, 'const')
        self.type = ConstType(tokens)
        self._name = Identifier(tokens)
        self._equals = Symbol(tokens, '=')
        self.value = ConstValue(tokens)
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        """Get construct type."""
        return 'const'

    @property
    def name(self):
        """Get name."""
        return self._name.name

    @property
    def method_name(self):
        """Get method name."""
        return None

    @property
    def method_names(self):
        """Get method names."""
        return []

    @property
    def complexity_factor(self):
        """Get complexity factor."""
        return 0

    def _str(self):
        """Convert to string."""
        return str(self._const) + str(self.type) + str(self._name) + str(self._equals) + str(self.value)

    def _markup(self, generator):
        self._const.markup(generator)
        generator.add_type(self.type)
        self._name.markup(generator)
        generator.add_text(self._equals)
        self.value.markup(generator)
        return self

    def __repr__(self):
        """Debug info."""
        return ('[Const: ' + repr(self.type)
                + '[name: ' + repr(self._name) + '] = [value: ' + str(self.value) + ']]')


class Enum(Construct):
    """
    WebIDL "enum".

    Syntax:
    [ExtendedAttributes] "enum" Identifier "{" EnumValueList "}" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        token = tokens.peek()
        if (token and token.is_symbol('enum')):
            if (Identifier.peek(tokens)):
                token = tokens.peek()
                if (token and token.is_symbol('{')):
                    if (EnumValueList.peek(tokens)):
                        token = tokens.peek()
                        return tokens.pop_position(token and token.is_symbol('}'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self._enum = Symbol(tokens, 'enum')
        self._name = Identifier(tokens)
        self._open_brace = Symbol(tokens, '{')
        self.values = EnumValueList(tokens)
        self._close_brace = Symbol(tokens, '}')
        self._consume_semicolon(tokens, False)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'enum'

    @property
    def name(self):
        return self._name.name

    def _str(self):
        return Construct._str(self) + str(self._enum) + str(self._name) + str(self._open_brace) + str(self.values) + str(self._close_brace)

    def _markup(self, generator):
        self._enum.markup(generator)
        self._name.markup(generator)
        generator.add_text(self._open_brace)
        self.values.markup(generator)
        generator.add_text(self._close_brace)
        return self

    def __repr__(self):
        return ('[Enum: ' + Construct.__repr__(self) + '[name: ' + repr(self._name) + '] '
                + '[values: ' + repr(self.values) + ']]')


class Typedef(Construct):
    """
    WebIDL "typedef".

    Syntax:
    [ExtendedAttributes] "typedef" TypeWithExtendedAttributes Identifier ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        if (Symbol.peek(tokens, 'typedef')):
            if (TypeWithExtendedAttributes.peek(tokens)):
                return tokens.pop_position(Identifier.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self._typedef = Symbol(tokens, 'typedef')
        self.type = TypeWithExtendedAttributes(tokens)
        self._name = Identifier(tokens)
        self._consume_semicolon(tokens)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'typedef'

    @property
    def name(self):
        return self._name.name

    def _str(self):
        output = Construct._str(self) + str(self._typedef)
        return output + str(self.type) + str(self._name)

    def _markup(self, generator):
        self._typedef.markup(generator)
        generator.add_type(self.type)
        self._name.markup(generator)
        return self

    def __repr__(self):
        output = '[Typedef: ' + Construct.__repr__(self)
        return output + repr(self.type) + ' [name: ' + self.name + ']]'


class Argument(Construct):
    """
    WebIDL method argument.

    Syntax:
    [ExtendedAttributeList] "optional" [IgnoreInOut] TypeWithExtendedAttributes ArgumentName [Default]
    | [ExtendedAttributeList] [IgnoreInOut] Type ["..."] ArgumentName
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        IgnoreInOut.peek(tokens)
        if (Type.peek(tokens)):
            Symbol.peek(tokens, '...')
            return tokens.pop_position(ArgumentName.peek(tokens))
        else:
            if (Symbol.peek(tokens, 'optional')):
                IgnoreInOut.peek(tokens)
                if (TypeWithExtendedAttributes.peek(tokens)):
                    if (ArgumentName.peek(tokens)):
                        Default.peek(tokens)
                        return tokens.pop_position(True)
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent)
        if (Symbol.peek(tokens, 'optional')):
            self.optional = Symbol(tokens, 'optional')
            self._ignore = IgnoreInOut(tokens) if (IgnoreInOut.peek(tokens)) else None
            self.type = TypeWithExtendedAttributes(tokens)
            self.variadic = None
            self._name = ArgumentName(tokens)
            self.default = Default(tokens) if (Default.peek(tokens)) else None
        else:
            self.optional = None
            self._ignore = IgnoreInOut(tokens) if (IgnoreInOut.peek(tokens)) else None
            self.type = Type(tokens)
            self.variadic = Symbol(tokens, '...') if (Symbol.peek(tokens, '...')) else None
            self._name = ArgumentName(tokens)
            self.default = None
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'argument'

    @property
    def name(self):
        return self._name.name

    @property
    def required(self):
        return ((self.optional is None) and (self.variadic is None))

    def _str(self):
        output = Construct._str(self)
        output += str(self.optional) if (self.optional) else ''
        output += str(self._ignore) if (self._ignore) else ''
        output += str(self.type)
        output += str(self.variadic) if (self.variadic) else ''
        return output + str(self._name) + (str(self.default) if (self.default) else '')

    def _markup(self, generator):
        if (self.optional):
            self.optional.markup(generator)
        if (self._ignore):
            self._ignore.markup(generator)
        generator.add_type(self.type)
        generator.add_text(self.variadic)
        self._name.markup(generator)
        if (self.default):
            self.default.markup(generator)
        return self

    def __repr__(self):
        output = '[Argument: ' + Construct.__repr__(self)
        output += '[optional] ' if (self.optional) else ''
        output += '[type: ' + str(self.type) + ']'
        output += '[...] ' if (self.variadic) else ' '
        output += '[name: ' + repr(self._name) + ']'
        return output + ((' [default: ' + repr(self.default) + ']]') if (self.default) else ']')


class InterfaceMember(Construct):
    """
    WebIDL interface member.

    Syntax:
    [ExtendedAttributes] Constructor | Const | Operation | SpecialOperation | Stringifier | StaticMember | AsyncIterable
    | Iterable | Attribute | Maplike | Setlike
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        return tokens.pop_position(Constructor.peek(tokens) or Const.peek(tokens)
                                   or Stringifier.peek(tokens) or StaticMember.peek(tokens)
                                   or AsyncIterable.peek(tokens) or Iterable.peek(tokens)
                                   or Maplike.peek(tokens) or Setlike.peek(tokens)
                                   or Attribute.peek(tokens)
                                   or SpecialOperation.peek(tokens) or Operation.peek(tokens))

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent)
        if (Constructor.peek(tokens)):
            self.member = Constructor(tokens, parent)
        elif (Const.peek(tokens)):
            self.member = Const(tokens, parent)
        elif (Stringifier.peek(tokens)):
            self.member = Stringifier(tokens, parent)
        elif (StaticMember.peek(tokens)):
            self.member = StaticMember(tokens, parent)
        elif (AsyncIterable.peek(tokens)):
            self.member = AsyncIterable(tokens, parent)
        elif (Iterable.peek(tokens)):
            self.member = Iterable(tokens, parent)
        elif (Maplike.peek(tokens)):
            self.member = Maplike(tokens, parent)
        elif (Setlike.peek(tokens)):
            self.member = Setlike(tokens, parent)
        elif (Attribute.peek(tokens)):
            self.member = Attribute(tokens, parent)
        elif (SpecialOperation.peek(tokens)):
            self.member = SpecialOperation(tokens, parent)
        else:
            self.member = Operation(tokens, parent)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return self.member.idl_type

    @property
    def name(self):
        return self.member.name

    @property
    def method_name(self):
        return self.member.method_name

    @property
    def method_names(self):
        return self.member.method_names

    @property
    def normal_name(self):
        return self.method_name if (self.method_name) else self.name

    @property
    def arguments(self):
        return self.member.arguments

    def find_argument(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            for argument in self.member.arguments:
                if (name == argument.name):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            return [argument for argument in self.member.arguments if (name == argument.name)]
        return []

    def matches_argument_names(self, argument_names):
        if (self.arguments):
            return self.arguments.matches_names(argument_names)
        return (not argument_names)

    def _str(self):
        return Construct._str(self) + str(self.member)

    def _markup(self, generator):
        return self.member._markup(generator)

    def __repr__(self):
        output = '[Member: ' + Construct.__repr__(self)
        return output + repr(self.member) + ']'


class MixinMember(Construct):
    """
    WebIDL mixin member.

    Syntax:
    [ExtendedAttributes] Const | Operation | Stringifier | ReadOnly AttributeRest
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        return tokens.pop_position(Const.peek(tokens) or Stringifier.peek(tokens)
                                   or MixinAttribute.peek(tokens) or Operation.peek(tokens))

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent)
        if (Const.peek(tokens)):
            self.member = Const(tokens, parent)
        elif (Stringifier.peek(tokens)):
            self.member = Stringifier(tokens, parent)
        elif (MixinAttribute.peek(tokens)):
            self.member = MixinAttribute(tokens, parent)
        else:
            self.member = Operation(tokens, parent)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return self.member.idl_type

    @property
    def name(self):
        return self.member.name

    @property
    def method_name(self):
        return self.member.method_name

    @property
    def method_names(self):
        return self.member.method_names

    @property
    def normal_name(self):
        return self.method_name if (self.method_name) else self.name

    @property
    def arguments(self):
        return self.member.arguments

    def find_argument(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            for argument in self.member.arguments:
                if (name == argument.name):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            return [argument for argument in self.member.arguments if (name == argument.name)]
        return []

    def matches_argument_names(self, argument_names):
        if (self.arguments):
            return self.arguments.matches_names(argument_names)
        return (not argument_names)

    def _str(self):
        return Construct._str(self) + str(self.member)

    def _markup(self, generator):
        return self.member._markup(generator)

    def __repr__(self):
        output = '[Member: ' + Construct.__repr__(self)
        return output + repr(self.member) + ']'


class SyntaxError(Construct):
    """
    Capture invalid syntax.

    Syntax:
    ... ";" | ... "}"
    """

    def __init__(self, tokens, parent, parser = None):
        Construct.__init__(self, tokens, parent, False, parser = parser)
        self.tokens = tokens.syntax_error((';', '}'), False)
        if ((1 < len(self.tokens)) and self.tokens[-1].is_symbol('}')):
            tokens.restore(self.tokens[-1])
            self.tokens = self.tokens[:-1]
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'unknown'

    @property
    def name(self):
        return None

    @property
    def required(self):
        return False

    def _str(self):
        return ''.join([str(token) for token in self.tokens])

    def __repr__(self):
        output = '[Unknown: ' + Construct.__repr__(self) + ' tokens: '
        return output + ''.join([repr(token) for token in self.tokens]) + ']'


class Interface(Construct):
    """
    WebIDL "interface".

    Syntax:
    [ExtendedAttributes] ["partial"] "interface" Identifier [Inheritance] "{" [InterfaceMember]... "}" ";"
    """

    @classmethod
    def peek(cls, tokens, accept_extended_attributes = True):
        tokens.push_position(False)
        if (accept_extended_attributes):
            Construct.peek(tokens)
        Symbol.peek(tokens, 'partial')
        if (Symbol.peek(tokens, 'interface')):
            if (Identifier.peek(tokens)):
                Inheritance.peek(tokens)
                return tokens.pop_position(Symbol.peek(tokens, '{'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, (not parent), parser = parser)
        self.partial = Symbol(tokens, 'partial') if (Symbol.peek(tokens, 'partial')) else None
        self._interface = Symbol(tokens, 'interface')
        self._name = Identifier(tokens)
        self.inheritance = Inheritance(tokens) if (Inheritance.peek(tokens)) else None
        self._open_brace = Symbol(tokens, '{')
        self.members = self.constructors
        self._close_brace = None
        while (tokens.has_tokens()):
            if (Symbol.peek(tokens, '}')):
                self._close_brace = Symbol(tokens, '}')
                break
            if (InterfaceMember.peek(tokens)):
                self.members.append(InterfaceMember(tokens, parent if (parent) else self))
            else:
                self.members.append(SyntaxError(tokens, parent if (parent) else self))
        self._consume_semicolon(tokens, False)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'interface'

    @property
    def name(self):
        return self._name.name

    @property
    def complexity_factor(self):
        return len(self.members) + 1

    def __len__(self):
        return len(self.members)

    def keys(self):
        return [member.name for member in self.members]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return member
            return None
        return self.members[key]

    def __iter__(self):
        return iter(self.members)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return True
            return False
        return (key in self.members)

    def find_member(self, name):
        for member in reversed(self.members):
            if (name == member.name):
                return member
        return None

    def find_members(self, name):
        return [member for member in self.members if (name == member.name)]

    def find_method(self, name, argument_names=None):
        for member in reversed(self.members):
            if (('method' == member.idl_type) and (name == member.name)
                    and ((argument_names is None) or member.matches_argument_names(argument_names))):
                return member
        return None

    def find_methods(self, name, argument_names=None):
        return [member for member in self.members if (('method' == member.idl_type) and (name == member.name)
                                                      and ((argument_names is None) or member.matches_argument_names(argument_names)))]

    def find_argument(self, name, search_members = True):
        if (search_members):
            for member in reversed(self.members):
                argument = member.find_argument(name)
                if (argument):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        result = []
        if (search_members):
            for member in self.members:
                result += member.find_arguments(name)
        return result

    def _str(self):
        output = Construct._str(self)
        output += str(self.partial) if (self.partial) else ''
        output += str(self._interface) + str(self._name)
        output += str(self.inheritance) if (self.inheritance) else ''
        output += str(self._open_brace)
        for member in self.members:
            if ('constructor' != member.idl_type):
                output += str(member)
        return output + str(self._close_brace) if (self._close_brace) else output

    def _markup(self, generator):
        if (self.partial):
            self.partial.markup(generator)
        self._interface.markup(generator)
        self._name.markup(generator)
        if (self.inheritance):
            self.inheritance.markup(generator)
        generator.add_text(self._open_brace)
        for member in self.members:
            if ('constructor' != member.idl_type):
                member.markup(generator)
        generator.add_text(self._close_brace)
        return self

    def __repr__(self):
        output = '[Interface: ' + Construct.__repr__(self)
        output += '[partial] ' if (self.partial) else ''
        output += '[name: ' + repr(self._name) + '] '
        output += repr(self.inheritance) if (self.inheritance) else ''
        output += '[members: \n'
        for member in self.members:
            output += '  ' + repr(member) + '\n'
        return output + ']]'


class Mixin(Construct):
    """
    WebIDL "interface mixin".

    Syntax:
    [ExtendedAttributes] ["partial"] "interface" "mixin" Identifier [Inheritance] "{" [MixinMember]... "}" ";"
    """

    @classmethod
    def peek(cls, tokens, accept_extended_attributes = True):
        tokens.push_position(False)
        if (accept_extended_attributes):
            Construct.peek(tokens)
        Symbol.peek(tokens, 'partial')
        if (Symbol.peek(tokens, 'interface') and Symbol.peek(tokens, 'mixin')):
            if (Identifier.peek(tokens)):
                Inheritance.peek(tokens)
                return tokens.pop_position(Symbol.peek(tokens, '{'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, (not parent), parser = parser)
        self.partial = Symbol(tokens, 'partial') if (Symbol.peek(tokens, 'partial')) else None
        self._interface = Symbol(tokens, 'interface')
        self._mixin = Symbol(tokens, 'mixin')
        self._name = Identifier(tokens)
        self.inheritance = Inheritance(tokens) if (Inheritance.peek(tokens)) else None
        self._open_brace = Symbol(tokens, '{')
        self.members = self.constructors
        self._close_brace = None
        while (tokens.has_tokens()):
            if (Symbol.peek(tokens, '}')):
                self._close_brace = Symbol(tokens, '}')
                break
            if (MixinMember.peek(tokens)):
                self.members.append(MixinMember(tokens, parent if (parent) else self))
            else:
                self.members.append(SyntaxError(tokens, parent if (parent) else self))
        self._consume_semicolon(tokens, False)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'interface'

    @property
    def name(self):
        return self._name.name

    @property
    def complexity_factor(self):
        return len(self.members) + 1

    def __len__(self):
        return len(self.members)

    def keys(self):
        return [member.name for member in self.members]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return member
            return None
        return self.members[key]

    def __iter__(self):
        return iter(self.members)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return True
            return False
        return (key in self.members)

    def find_member(self, name):
        for member in reversed(self.members):
            if (name == member.name):
                return member
        return None

    def find_members(self, name):
        return [member for member in self.members if (name == member.name)]

    def find_method(self, name, argument_names=None):
        for member in reversed(self.members):
            if (('method' == member.idl_type) and (name == member.name)
                    and ((argument_names is None) or member.matches_argument_names(argument_names))):
                return member
        return None

    def find_methods(self, name, argument_names=None):
        return [member for member in self.members if (('method' == member.idl_type) and (name == member.name)
                                                      and ((argument_names is None) or member.matches_argument_names(argument_names)))]

    def find_argument(self, name, search_members = True):
        if (search_members):
            for member in reversed(self.members):
                argument = member.find_argument(name)
                if (argument):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        result = []
        if (search_members):
            for member in self.members:
                result += member.find_arguments(name)
        return result

    def _str(self):
        output = Construct._str(self)
        output += str(self.partial) if (self.partial) else ''
        output += str(self._interface) + str(self._mixin) + str(self._name)
        output += str(self.inheritance) if (self.inheritance) else ''
        output += str(self._open_brace)
        for member in self.members:
            if ('constructor' != member.idl_type):
                output += str(member)
        return output + str(self._close_brace) if (self._close_brace) else output

    def _markup(self, generator):
        if (self.partial):
            self.partial.markup(generator)
        self._interface.markup(generator)
        self._mixin.markup(generator)
        self._name.markup(generator)
        if (self.inheritance):
            self.inheritance.markup(generator)
        generator.add_text(self._open_brace)
        for member in self.members:
            if ('constructor' != member.idl_type):
                member.markup(generator)
        generator.add_text(self._close_brace)
        return self

    def __repr__(self):
        output = '[Interface: ' + Construct.__repr__(self)
        output += '[partial] ' if (self.partial) else ''
        output += '[mixin] '
        output += '[name: ' + repr(self._name) + '] '
        output += repr(self.inheritance) if (self.inheritance) else ''
        output += '[members: \n'
        for member in self.members:
            output += '  ' + repr(member) + '\n'
        return output + ']]'


class NamespaceMember(Construct):
    """
    WebIDL namespace member.

    Syntax:
    [ExtendedAttributes] Operation | "readonly" Attribute
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        if (Symbol.peek(tokens, 'readonly')):
            return tokens.pop_position(Attribute.peek(tokens))
        return tokens.pop_position(Operation.peek(tokens))

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent)
        token = tokens.sneak_peek()
        if (token.is_symbol('readonly')):
            self.member = Attribute(tokens, parent)
        else:
            self.member = Operation(tokens, parent)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return self.member.idl_type

    @property
    def name(self):
        return self.member.name

    @property
    def method_name(self):
        return self.member.method_name

    @property
    def method_names(self):
        return self.member.method_names

    @property
    def normal_name(self):
        return self.method_name if (self.method_name) else self.name

    @property
    def arguments(self):
        return self.member.arguments

    def find_argument(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            for argument in self.member.arguments:
                if (name == argument.name):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        if (hasattr(self.member, 'arguments') and self.member.arguments):
            return [argument for argument in self.member.arguments if (name == argument.name)]
        return []

    def matches_argument_names(self, argument_names):
        if (self.arguments):
            return self.arguments.matches_names(argument_names)
        return (not argument_names)

    def _str(self):
        return Construct._str(self) + str(self.member)

    def _markup(self, generator):
        return self.member._markup(generator)

    def __repr__(self):
        output = '[Member: ' + Construct.__repr__(self)
        return output + repr(self.member) + ']'


class Namespace(Construct):
    """
    WebIDL "namespace".

    Syntax:
    [ExtendedAttributes] ["partial"] "namespace" Identifier "{" [NamespaceMember]... "}" ";"
    """

    @classmethod
    def peek(cls, tokens, accept_extended_attributes = True):
        tokens.push_position(False)
        if (accept_extended_attributes):
            Construct.peek(tokens)
        Symbol.peek(tokens, 'partial')
        if (Symbol.peek(tokens, 'namespace')):
            if (Identifier.peek(tokens)):
                return tokens.pop_position(Symbol.peek(tokens, '{'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, (not parent), parser = parser)
        self.partial = Symbol(tokens, 'partial') if (Symbol.peek(tokens, 'partial')) else None
        self._namespace = Symbol(tokens, 'namespace')
        self._name = Identifier(tokens)
        self._open_brace = Symbol(tokens, '{')
        self.members = []
        self._close_brace = None
        while (tokens.has_tokens()):
            if (Symbol.peek(tokens, '}')):
                self._close_brace = Symbol(tokens, '}')
                break
            if (NamespaceMember.peek(tokens)):
                self.members.append(NamespaceMember(tokens, parent if (parent) else self))
            else:
                self.members.append(SyntaxError(tokens, parent if (parent) else self))
        self._consume_semicolon(tokens, False)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'namespace'

    @property
    def name(self):
        return self._name.name

    @property
    def complexity_factor(self):
        return len(self.members) + 1

    def __len__(self):
        return len(self.members)

    def keys(self):
        return [member.name for member in self.members]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return member
            return None
        return self.members[key]

    def __iter__(self):
        return iter(self.members)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return True
            return False
        return (key in self.members)

    def find_member(self, name):
        for member in reversed(self.members):
            if (name == member.name):
                return member
        return None

    def find_members(self, name):
        return [member for member in self.members if (name == member.name)]

    def find_method(self, name, argument_names=None):
        for member in reversed(self.members):
            if (('method' == member.idl_type) and (name == member.name)
                    and ((argument_names is None) or member.matches_argument_names(argument_names))):
                return member
        return None

    def find_methods(self, name, argument_names=None):
        return [member for member in self.members if (('method' == member.idl_type) and (name == member.name)
                                                      and ((argument_names is None) or member.matches_argument_names(argument_names)))]

    def find_argument(self, name, search_members = True):
        if (search_members):
            for member in reversed(self.members):
                argument = member.find_argument(name)
                if (argument):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        result = []
        if (search_members):
            for member in self.members:
                result += member.find_arguments(name)
        return result

    def _str(self):
        output = Construct._str(self)
        output += str(self.partial) if (self.partial) else ''
        output += str(self._namespace) + str(self._name)
        output += str(self._open_brace)
        for member in self.members:
            output += str(member)
        return output + str(self._close_brace) if (self._close_brace) else output

    def _markup(self, generator):
        if (self.partial):
            self.partial.markup(generator)
        self._namespace.markup(generator)
        self._name.markup(generator)
        generator.add_text(self._open_brace)
        for member in self.members:
            member.markup(generator)
        generator.add_text(self._close_brace)
        return self

    def __repr__(self):
        output = '[Namespace: ' + Construct.__repr__(self)
        output += '[partial] ' if (self.partial) else ''
        output += '[name: ' + repr(self._name) + '] '
        output += '[members: \n'
        for member in self.members:
            output += '  ' + repr(member) + '\n'
        return output + ']]'


class DictionaryMember(Construct):
    """
    WebIDL dictionary member.

    Syntax:
    [ExtendedAttributes] ["required"] TypeWithExtendedAttributes Identifier [Default] ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        Symbol.peek(tokens, 'required')
        if (TypeWithExtendedAttributes.peek(tokens)):
            if (Identifier.peek(tokens)):
                Default.peek(tokens)
                return tokens.pop_position(True)
        tokens.pop_position(False)

    def __init__(self, tokens, parent = None):
        Construct.__init__(self, tokens, parent)
        self.required = Symbol(tokens, 'required') if (Symbol.peek(tokens, 'required')) else None
        self.type = TypeWithExtendedAttributes(tokens)
        self._name = Identifier(tokens)
        self.default = Default(tokens) if (Default.peek(tokens)) else None
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'dict-member'

    @property
    def name(self):
        return self._name.name

    def _str(self):
        output = Construct._str(self)
        output += str(self.required) if (self.required) else ''
        output += str(self.type) + str(self._name)
        return output + (str(self.default) if (self.default) else '')

    def _markup(self, generator):
        if (self.required):
            self.required.markup(generator)
        generator.add_type(self.type)
        self._name.markup(generator)
        if (self.default):
            self.default.markup(generator)
        return self

    def __repr__(self):
        output = '[DictionaryMember: ' + Construct.__repr__(self)
        output += '[required] ' if (self.required) else ''
        output += repr(self.type)
        output += ' [name: ' + repr(self._name) + ']'
        if (self.default):
            output += ' = [default: ' + repr(self.default) + ']'
        output += ']'
        return output


class Dictionary(Construct):
    """
    WebIDL "dictionary".

    Syntax:
    [ExtendedAttributes] ["partial"] "dictionary" Identifier [Inheritance] "{" [DictionaryMember]... "}" ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        Symbol.peek(tokens, 'partial')
        if (Symbol.peek(tokens, 'dictionary')):
            if (Identifier.peek(tokens)):
                Inheritance.peek(tokens)
                return tokens.pop_position(Symbol.peek(tokens, '{'))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self.partial = Symbol(tokens, 'partial') if (Symbol.peek(tokens, 'partial')) else None
        self._dictionary = Symbol(tokens, 'dictionary')
        self._name = Identifier(tokens)
        self.inheritance = Inheritance(tokens) if (Inheritance.peek(tokens)) else None
        self._open_brace = Symbol(tokens, '{')
        self.members = []
        self._close_brace = None
        while (tokens.has_tokens()):
            if (Symbol.peek(tokens, '}')):
                self._close_brace = Symbol(tokens, '}')
                break
            if (DictionaryMember.peek(tokens)):
                self.members.append(DictionaryMember(tokens, self))
            else:
                self.members.append(SyntaxError(tokens, self))
        self._consume_semicolon(tokens, False)
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'dictionary'

    @property
    def name(self):
        return self._name.name

    @property
    def complexity_factor(self):
        return len(self.members) + 1

    @property
    def required(self):
        for member in self.members:
            if (member.required):
                return True
        return False

    def __len__(self):
        return len(self.members)

    def keys(self):
        return [member.name for member in self.members]

    def __getitem__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return member
            return None
        return self.members[key]

    def __iter__(self):
        return iter(self.members)

    def __contains__(self, key):
        if (isinstance(key, str)):
            for member in self.members:
                if (key == member.name):
                    return True
            return False
        return (key in self.members)

    def find_member(self, name):
        for member in reversed(self.members):
            if (name == member.name):
                return member
        return None

    def find_members(self, name):
        return [member for member in self.members if (name == member.name)]

    def _str(self):
        output = Construct._str(self)
        output += str(self.partial) if (self.partial) else ''
        output += str(self._dictionary) + str(self._name)
        output += str(self.inheritance) if (self.inheritance) else ''
        output += str(self._open_brace)
        for member in self.members:
            output += str(member)
        return output + str(self._close_brace) if (self._close_brace) else output

    def _markup(self, generator):
        if (self.partial):
            self.partial.markup(generator)
        self._dictionary.markup(generator)
        self._name.markup(generator)
        if (self.inheritance):
            self.inheritance.markup(generator)
        generator.add_text(self._open_brace)
        for member in self.members:
            member.markup(generator)
        generator.add_text(self._close_brace)
        return self

    def __repr__(self):
        output = '[Dictionary: ' + Construct.__repr__(self)
        output += '[partial] ' if (self.partial) else ''
        output += '[name: ' + repr(self._name) + '] '
        output += repr(self.inheritance) if (self.inheritance) else ''
        output += '[members: \n'
        for member in self.members:
            output += '  ' + repr(member) + '\n'
        return output + ']]'


class Callback(Construct):
    """
    WebIDL "callback".

    Syntax:
    [ExtendedAttributes] "callback" Identifier "=" ReturnType "(" [ArgumentList] ")" ";"
    | [ExtendedAttributes] "callback" Interface
    | [ExtendedAttributes] "callback" Mixin
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        if (Symbol.peek(tokens, 'callback')):
            if (Mixin.peek(tokens, False)):
                return tokens.pop_position(True)
            if (Interface.peek(tokens, False)):
                return tokens.pop_position(True)
            if (Identifier.peek(tokens)):
                if (Symbol.peek(tokens, '=')):
                    if (ReturnType.peek(tokens)):
                        if (Symbol.peek(tokens, '(')):
                            ArgumentList.peek(tokens)
                            token = tokens.peek()
                            return tokens.pop_position(token and token.is_symbol(')'))
        tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self._callback = Symbol(tokens, 'callback')
        token = tokens.sneak_peek()
        if (token.is_identifier()):
            self._name = Identifier(tokens)
            self._equals = Symbol(tokens, '=')
            self.return_type = ReturnType(tokens)
            self._open_paren = Symbol(tokens, '(')
            self.arguments = ArgumentList(tokens, self) if (ArgumentList.peek(tokens)) else None
            self._close_paren = Symbol(tokens, ')')
            self.interface = None
            self._consume_semicolon(tokens)
        else:
            self._equals = None
            self.return_type = None
            self._open_paren = None
            self.arguments = None
            self._close_paren = None
            if (Mixin.peek(tokens, False)):
                self.interface = Mixin(tokens, self)
            else:
                self.interface = Interface(tokens, self)
            self._name = self.interface._name
        self._did_parse(tokens)
        self.parser.add_type(self)

    @property
    def idl_type(self):
        return 'callback'

    @property
    def name(self):
        return self._name.name

    @property
    def complexity_factor(self):
        return self.interface.complexity_factor if (self.interface) else 1

    def __len__(self):
        return len(self.interface.members) if (self.interface) else 0

    def keys(self):
        return [member.name for member in self.interface.members] if (self.interface) else []

    def __getitem__(self, key):
        if (self.interface):
            if (isinstance(key, str)):
                for member in self.interface.members:
                    if (key == member.name):
                        return member
                return None
            return self.members[key]
        return None

    def __iter__(self):
        if (self.interface):
            return iter(self.interface.members)
        return iter(())

    def __contains__(self, key):
        if (self.interface):
            if (isinstance(key, str)):
                for member in self.interface.members:
                    if (key == member.name):
                        return True
                return False
            return (key in self.interface.members)
        return False

    def find_member(self, name):
        if (self.interface):
            for member in reversed(self.interface.members):
                if (name == member.name):
                    return member
        return None

    def find_members(self, name):
        if (self.interface):
            return [member for member in self.interface.members if (name == member.name)]
        return []

    def find_argument(self, name, search_members = True):
        if (self.arguments):
            for argument in self.arguments:
                if (name == argument.name):
                    return argument
        if (self.interface and search_members):
            for member in reversed(self.interface.members):
                argument = member.find_argument(name)
                if (argument):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        result = []
        if (self.arguments):
            result = [argument for argument in self.arguments if (name == argument.name)]
        if (self.interface and search_members):
            for member in self.interface.members:
                result += member.find_arguments(name)
        return result

    def _str(self):
        output = Construct._str(self) + str(self._callback)
        if (self.interface):
            return output + str(self.interface)
        output += str(self._name) + str(self._equals) + str(self.return_type)
        return output + str(self._open_paren) + (str(self.arguments) if (self.arguments) else '') + str(self._close_paren)

    def _markup(self, generator):
        self._callback.markup(generator)
        if (self.interface):
            return self.interface._markup(generator)
        self._name.markup(generator)
        generator.add_text(self._equals)
        self.return_type.markup(generator)
        generator.add_text(self._open_paren)
        if (self.arguments):
            self.arguments.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        output = '[Callback: ' + Construct.__repr__(self)
        if (self.interface):
            return output + repr(self.interface) + ']'
        output += '[name: ' + self.name + '] [return_type: ' + str(self.return_type) + '] '
        return output + '[ArgumentList: ' + (repr(self.arguments) if (self.arguments) else '') + ']]'


class ImplementsStatement(Construct):
    """
    WebIDL "implements".

    Syntax:
    [ExtendedAttributes] Identifier "implements" Identifier ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        Construct.peek(tokens)
        if (TypeIdentifier.peek(tokens)):
            if (Symbol.peek(tokens, 'implements')):
                return tokens.pop_position(TypeIdentifier.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self._name = TypeIdentifier(tokens)
        self._implements_symbol = Symbol(tokens, 'implements')
        self._implements = TypeIdentifier(tokens)
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'implements'

    @property
    def name(self):
        return self._name.name

    @property
    def implements(self):
        return self._implements.name

    def _str(self):
        return Construct._str(self) + str(self._name) + str(self._implements_symbol) + str(self._implements)

    def _markup(self, generator):
        self._name.markup(generator)
        self._implements_symbol.markup(generator)
        self._implements.markup(generator)
        return self

    def __repr__(self):
        return '[Implements: ' + Construct.__repr__(self) + '[name: ' + repr(self._name) + '] [Implements: ' + repr(self._implements) + ']]'


class IncludesStatement(Construct):
    """
    WebIDL "includes".

    Syntax:
    Identifier "includes" Identifier ";"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (TypeIdentifier.peek(tokens)):
            if (Symbol.peek(tokens, 'includes')):
                return tokens.pop_position(TypeIdentifier.peek(tokens))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent = None, parser = None):
        Construct.__init__(self, tokens, parent, parser = parser)
        self._name = TypeIdentifier(tokens)
        self._includes_symbol = Symbol(tokens, 'includes')
        self._includes = TypeIdentifier(tokens)
        self._consume_semicolon(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'includes'

    @property
    def name(self):
        return self._name.name

    @property
    def includes(self):
        return self._includes.name

    def _str(self):
        return Construct._str(self) + str(self._name) + str(self._includes_symbol) + str(self._includes)

    def _markup(self, generator):
        self._name.markup(generator)
        self._includes_symbol.markup(generator)
        self._includes.markup(generator)
        return self

    def __repr__(self):
        return '[Includes: ' + Construct.__repr__(self) + '[name: ' + repr(self._name) + '] [Includes: ' + repr(self._includes) + ']]'


class ExtendedAttributeUnknown(Construct):
    """
    WebIDL unknown extended attribute.

    Syntax:
    list of tokens
    """

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        skipped = tokens.seek_symbol((',', ']'))
        self.tokens = skipped[:-1]
        tokens.restore(skipped[-1])
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'extended-attribute'

    @property
    def name(self):
        return None

    def _str(self):
        return ''.join([str(token) for token in self.tokens])

    def __repr__(self):
        return '[ExtendedAttribute: ' + ''.join([repr(token) for token in self.tokens]) + ']'


class ExtendedAttributeNoArgs(Construct):
    """
    WebIDL extended attribute without arguments.

    Syntax:
    Identifier
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            token = tokens.sneak_peek()
            return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'constructor' if ('Constructor' == self.attribute) else 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def name(self):
        return self.parent.name if ('constructor' == self.idl_type) else self.attribute

    @property
    def normal_name(self):
        return (self.parent.name + '()') if ('constructor' == self.idl_type) else self.attribute

    def _str(self):
        return str(self._attribute)

    def _markup(self, generator):
        self._attribute.markup(generator)
        return self

    def __repr__(self):
        return '[ExtendedAttributeNoArgs: ' + repr(self._attribute) + ']'


class ExtendedAttributeArgList(Construct):
    """
    WebIDL extended attribute with argument list.

    Syntax:
    Identifier "(" [ArgumentList] ")"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            if (Symbol.peek(tokens, '(')):
                ArgumentList.peek(tokens)
                if (Symbol.peek(tokens, ')')):
                    token = tokens.sneak_peek()
                    return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._open_paren = Symbol(tokens, '(')
        self.arguments = ArgumentList(tokens, self) if (ArgumentList.peek(tokens)) else None
        self._close_paren = Symbol(tokens, ')')
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'constructor' if ('Constructor' == self.attribute) else 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def name(self):
        return self.parent.name if ('constructor' == self.idl_type) else self.attribute

    @property
    def normal_name(self):
        if ('constructor' == self.idl_type):
            return self.parent.name + '(' + (', '.join(argument.name for argument in self.arguments) if (self.arguments) else '') + ')'
        return self.attribute

    def _str(self):
        return str(self._attribute) + str(self._open_paren) + (str(self.arguments) if (self.arguments) else '') + str(self._close_paren)

    def _markup(self, generator):
        self._attribute.markup(generator)
        generator.add_text(self._open_paren)
        if (self.arguments):
            self.arguments.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        return ('[ExtendedAttributeArgList: ' + repr(self._attribute)
                + ' [arguments: ' + (repr(self.arguments) if (self.arguments) else '') + ']]')


class ExtendedAttributeIdent(Construct):
    """
    WebIDL extended attribute with identifier.

    Syntax:
    Identifier "=" Identifier
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            if (Symbol.peek(tokens, '=')):
                if (Identifier.peek(tokens)):
                    token = tokens.sneak_peek()
                    return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._equals = Symbol(tokens, '=')
        self._value = TypeIdentifier(tokens)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'constructor' if ('NamedConstructor' == self.attribute) else 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def value(self):
        return self._value.name

    @property
    def name(self):
        return self.value if ('constructor' == self.idl_type) else self.attribute

    @property
    def normal_name(self):
        return (self.value + '()') if ('constructor' == self.idl_type) else self.attribute

    def _str(self):
        return str(self._attribute) + str(self._equals) + str(self._value)

    def _markup(self, generator):
        self._attribute.markup(generator)
        generator.add_text(self._equals)
        self._value.markup(generator)
        return self

    def __repr__(self):
        return ('[ExtendedAttributeIdent: ' + self.attribute + ' [value: ' + repr(self._value) + ']]')


class ExtendedAttributeIdentList(Construct):
    """
    WebIDL extended attribute with list of identifiers.

    Syntax:
    Identifier "=" "(" Identifier [Identifiers] ")"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            if (Symbol.peek(tokens, '=')):
                if (Symbol.peek(tokens, '(')):
                    if (TypeIdentifier.peek(tokens)):
                        TypeIdentifiers.peek(tokens)
                        if (Symbol.peek(tokens, ')')):
                            token = tokens.sneak_peek()
                            return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._equals = Symbol(tokens, '=')
        self._open_paren = Symbol(tokens, '(')
        self._value = TypeIdentifier(tokens)
        self.next = TypeIdentifiers(tokens) if (TypeIdentifiers.peek(tokens)) else None
        self._close_paren = Symbol(tokens, ')')
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'constructor' if ('NamedConstructor' == self.attribute) else 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def value(self):
        return self._value.name

    @property
    def name(self):
        return self.value if ('constructor' == self.idl_type) else self.attribute

    @property
    def normal_name(self):
        return (self.value + '()') if ('constructor' == self.idl_type) else self.attribute

    def _str(self):
        return (str(self._attribute) + str(self._equals) + str(self._open_paren) + str(self._value)
                + (str(self.next) if (self.next) else '') + str(self._close_paren))

    def _markup(self, generator):
        self._attribute.markup(generator)
        generator.add_text(self._equals)
        generator.add_text(self._open_paren)
        self._value.markup(generator)
        next = self.next
        while (next):
            generator.add_text(next._comma)
            next._name.markup(generator)
            next = next.next
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        return ('[ExtendedAttributeIdentList: ' + self.attribute + ' [value: ' + repr(self._value) + ']'
                + (repr(self.next) if (self.next) else '') + ']')


class ExtendedAttributeNamedArgList(Construct):
    """
    WebIDL extended attribute with named argument list.

    Syntax:
    Identifier "=" Identifier "(" [ArgumentList] ")"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            if (Symbol.peek(tokens, '=')):
                if (TypeIdentifier.peek(tokens)):
                    if (Symbol.peek(tokens, '(')):
                        ArgumentList.peek(tokens)
                        if (Symbol.peek(tokens, ')')):
                            token = tokens.sneak_peek()
                            return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._equals = Symbol(tokens, '=')
        self._value = TypeIdentifier(tokens)
        self._open_paren = Symbol(tokens, '(')
        self.arguments = ArgumentList(tokens, self) if (ArgumentList.peek(tokens)) else None
        self._close_paren = Symbol(tokens, ')')
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'constructor' if ('NamedConstructor' == self.attribute) else 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def value(self):
        return self._value.name

    @property
    def name(self):
        return self.value if ('constructor' == self.idl_type) else self.attribute

    @property
    def normal_name(self):
        if ('constructor' == self.idl_type):
            return self.value + '(' + (', '.join(argument.name for argument in self.arguments) if (self.arguments) else '') + ')'
        return self.attribute

    def _str(self):
        output = str(self._attribute) + str(self._equals) + str(self._value)
        return output + str(self._open_paren) + (str(self.arguments) if (self.arguments) else '') + str(self._close_paren)

    def _markup(self, generator):
        self._attribute.markup(generator)
        generator.add_text(self._equals)
        self._value.markup(generator)
        generator.add_text(self._open_paren)
        if (self.arguments):
            self.arguments.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        return ('[ExtendedAttributeNamedArgList: ' + repr(self._attribute) + ' [value: ' + repr(self._value) + ']'
                + ' [arguments: ' + (repr(self.arguments) if (self.arguments) else '') + ']]')


class ExtendedAttributeTypePair(Construct):
    """
    WebIDL extended attribute with type pair.

    Syntax:
    Identifier "(" Type "," Type ")"
    """

    @classmethod
    def peek(cls, tokens):
        tokens.push_position(False)
        if (Identifier.peek(tokens)):
            if (Symbol.peek(tokens, '(')):
                if (Type.peek(tokens)):
                    if (Symbol.peek(tokens, ',')):
                        if (Type.peek(tokens)):
                            if (Symbol.peek(tokens, ')')):
                                token = tokens.sneak_peek()
                                return tokens.pop_position((not token) or token.is_symbol((',', ']')))
        return tokens.pop_position(False)

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        self._attribute = Identifier(tokens)
        self._open_paren = Symbol(tokens, '(')
        self.key_type = Type(tokens)
        self._comma = Symbol(tokens, ',')
        self.value_type = Type(tokens)
        self._close_paren = Symbol(tokens, ')')
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return 'extended-attribute'

    @property
    def attribute(self):
        return self._attribute.name

    @property
    def name(self):
        return self.attribute

    def _str(self):
        output = str(self._attribute) + str(self._open_paren) + str(self.key_type) + str(self._comma)
        return output + str(self.value_type) + str(self._close_paren)

    def _markup(self, generator):
        self._attribute.markup(generator)
        generator.add_text(self._open_paren)
        self.key_type.markup(generator)
        generator.add_text(self._comma)
        self.value_type.markup(generator)
        generator.add_text(self._close_paren)
        return self

    def __repr__(self):
        return ('[ExtendedAttributeTypePair: ' + repr(self._attribute) + ' '
                + repr(self.key_type) + ' ' + repr(self.value_type) + ']')


class ExtendedAttribute(Construct):
    """
    WebIDL extended attribute.

    Syntax:
    ExtendedAttributeNoArgs | ExtendedAttributeArgList
    | ExtendedAttributeIdent | ExtendedAttributeNamedArgList
    | ExtendedAttributeIdentList | ExtendedAttributeTypePair
    """

    @classmethod
    def peek(cls, tokens):
        return (ExtendedAttributeNamedArgList.peek(tokens)
                or ExtendedAttributeArgList.peek(tokens)
                or ExtendedAttributeNoArgs.peek(tokens)
                or ExtendedAttributeTypePair.peek(tokens)
                or ExtendedAttributeIdentList(tokens)
                or ExtendedAttributeIdent.peek(tokens))

    def __init__(self, tokens, parent):
        Construct.__init__(self, tokens, parent, False)
        if (ExtendedAttributeNamedArgList.peek(tokens)):
            self.attribute = ExtendedAttributeNamedArgList(tokens, parent)
        elif (ExtendedAttributeArgList.peek(tokens)):
            self.attribute = ExtendedAttributeArgList(tokens, parent)
        elif (ExtendedAttributeNoArgs.peek(tokens)):
            self.attribute = ExtendedAttributeNoArgs(tokens, parent)
        elif (ExtendedAttributeTypePair.peek(tokens)):
            self.attribute = ExtendedAttributeTypePair(tokens, parent)
        elif (ExtendedAttributeIdentList.peek(tokens)):
            self.attribute = ExtendedAttributeIdentList(tokens, parent)
        elif (ExtendedAttributeIdent.peek(tokens)):
            self.attribute = ExtendedAttributeIdent(tokens, parent)
        else:
            self.attribute = ExtendedAttributeUnknown(tokens, parent)
        self._did_parse(tokens)

    @property
    def idl_type(self):
        return self.attribute.idl_type

    @property
    def name(self):
        return self.attribute.name

    @property
    def normal_name(self):
        return self.attribute.normal_name

    @property
    def arguments(self):
        if (hasattr(self.attribute, 'arguments')):
            return self.attribute.arguments
        return None

    def find_argument(self, name, search_members = True):
        if (hasattr(self.attribute, 'arguments') and self.attribute.arguments):
            for argument in self.attribute.arguments:
                if (name == argument.name):
                    return argument
        return None

    def find_arguments(self, name, search_members = True):
        if (hasattr(self.attribute, 'arguments') and self.attribute.arguments):
            return [argument for argument in self.attribute.arguments if (name == argument.name)]
        return []

    def matches_argument_names(self, argument_names):
        if (self.arguments):
            return self.arguments.matches_names(argument_names)
        return (not argument_names)

    def _str(self):
        return str(self.attribute)

    def _markup(self, generator):
        return self.attribute._markup(generator)

    def __repr__(self):
        return repr(self.attribute)
