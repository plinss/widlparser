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
"""Protocol definitions."""

from __future__ import annotations

from typing import Iterator, Optional, Sequence, TYPE_CHECKING, Tuple, Union

from typing_extensions import Protocol

if (TYPE_CHECKING):
	from .constructs import Construct


class SymbolTable(Protocol):
	"""Protocol for symbol capture and lookup."""

	def add_type(self, type: Construct) -> None:
		...

	def get_type(self, name: str) -> Optional[Construct]:
		...


class ConstructMap(Protocol):
	"""Mapping of name to Construct."""

	def __len__(self) -> int:
		...

	def __getitem__(self, key: Union[str, int]) -> Construct:
		...

	def __contains__(self, key: Union[str, int]) -> bool:
		...

	def __iter__(self) -> Iterator[Construct]:
		...

	def keys(self) -> Sequence[str]:
		...

	def values(self) -> Sequence[Construct]:
		...

	def items(self) -> Sequence[Tuple[str, Construct]]:
		...

	def get(self, key: Union[str, int]) -> Optional[Construct]:
		...


class Marker(Protocol):
	"""Protocol to provide markup."""

	def markup_construct(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_type(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_primitive_type(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_buffer_type(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_string_type(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_object_type(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_type_name(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_name(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_keyword(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def markup_enum_value(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:
		...

	def encode(self, text: str) -> str:
		...


class LegacyMarker(Protocol):
	"""Protocol to provide markup."""

	def markupConstruct(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupType(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupPrimitiveType(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupBufferType(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupStringType(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupObjectType(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupTypeName(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupName(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupKeyword(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def markupEnumValue(self, text: str, construct: Construct) -> Tuple[Optional[str], Optional[str]]:  # noqa: N802
		...

	def encode(self, text: str) -> str:
		...
