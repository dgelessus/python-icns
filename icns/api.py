import collections
import dataclasses
import os
import typing

from ._kaitai_struct import icns


_KSElement = icns.Icns.IconFamilyElement


def _decompress_icns_style_packbits(chunks: typing.Iterable[_KSElement.IcnsStylePackbits.Chunk]) -> typing.Iterable[bytes]:
	for chunk in chunks:
		if chunk.is_repeat:
			yield bytes([chunk.repeated_byte]) * chunk.repeat_count
		else:
			yield chunk.literal_data


class IconFamilyElement(object):
	type: bytes
	data: bytes
	_struct: _KSElement
	_parsed: "ParsedElement"
	
	def __init__(self, type: bytes, data: bytes, *, _struct: _KSElement) -> None:
		super().__init__()
		
		self.type = type
		self.data = data
		self._struct = _struct
	
	@classmethod
	def from_ks(cls, struct: _KSElement) -> "IconFamilyElement":
		return cls(struct.header.type.as_bytes, struct.data, _struct=struct)
	
	@property
	def parsed(self) -> "ParsedElement":
		try:
			return self._parsed
		except AttributeError:
			element_data_struct = self._struct.data_parsed
			if isinstance(element_data_struct, _KSElement.IconFamilyData):
				self._parsed = IconFamily.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.TableOfContentsData):
				self._parsed = TableOfContents.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconComposerVersionData):
				self._parsed = IconComposerVersion.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.InfoDictionaryData):
				self._parsed = InfoDictionary.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX1AndMaskData):
				self._parsed = Icon1BitAndMask.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX4Data):
				self._parsed = Icon4Bit.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX8Data):
				self._parsed = Icon8Bit.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconRgbData):
				self._parsed = IconRGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX8MaskData):
				self._parsed = Icon8BitMask.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconRgbZeroPrefixedData):
				self._parsed = IconRGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconArgbData):
				self._parsed = IconARGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconPngJp2Data):
				self._parsed = IconPNGOrJPEG2000.from_ks(element_data_struct)
			else:
				raise AssertionError(f"Unhandled KS element data type: {type(element_data_struct)}")
			
			return self._parsed


class ParsedElement(object):
	pass


@dataclasses.dataclass(frozen=True)
class IconFamily(ParsedElement):
	elements: typing.OrderedDict[bytes, IconFamilyElement]
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconFamilyData) -> "IconFamily":
		elements: typing.OrderedDict[bytes, IconFamilyElement] = collections.OrderedDict()
		
		for element_struct in struct.elements:
			element = IconFamilyElement.from_ks(element_struct)
			elements[element.type] = element
		
		return cls(elements)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO, *, ensure_root: bool = True) -> "IconFamily":
		if ensure_root:
			family_element = icns.Icns.from_io(stream).root_element
		else:
			family_element = _KSElement.from_io(stream)
		
		return cls.from_ks(family_element.data_parsed)
	
	@classmethod
	def from_file(cls, path: typing.Union[str, bytes, os.PathLike]):
		with open(path, "rb") as f:
			return cls.from_stream(f)


@dataclasses.dataclass(frozen=True)
class TableOfContents(ParsedElement):
	@dataclasses.dataclass()
	class Entry(object):
		type: bytes
		element_length: int
	
	entries: typing.List[Entry]
	
	@classmethod
	def from_ks(cls, struct: _KSElement.TableOfContentsData) -> "TableOfContents":
		return cls([
			TableOfContents.Entry(header.type.as_bytes, header.len_element)
			for header in struct.element_headers
		])


@dataclasses.dataclass(frozen=True)
class IconComposerVersion(ParsedElement):
	version: float
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconComposerVersionData) -> "IconComposerVersion":
		return cls(struct.version)


@dataclasses.dataclass(frozen=True)
class InfoDictionary(ParsedElement):
	archived_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.InfoDictionaryData) -> "InfoDictionary":
		return cls(struct.archived_data)


@dataclasses.dataclass(frozen=True)
class Icon(ParsedElement):
	point_width: int
	point_height: int
	scale: int
	
	@property
	def pixel_width(self) -> int:
		return self.point_width * self.scale
	
	@property
	def pixel_height(self) -> int:
		return self.point_height * self.scale


@dataclasses.dataclass(frozen=True)
class Icon1BitAndMask(Icon):
	icon_data: bytes
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX1AndMaskData) -> "Icon1BitAndMask":
		return cls(struct.width, struct.height, 1, struct.icon, struct.mask)


@dataclasses.dataclass(frozen=True)
class Icon4Bit(Icon):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX4Data) -> "Icon4Bit":
		return cls(struct.width, struct.height, 1, struct.icon)


@dataclasses.dataclass(frozen=True)
class Icon8Bit(Icon):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8Data) -> "Icon8Bit":
		return cls(struct.width, struct.height, 1, struct.icon)


class ICNSStylePackbits(object):
	compressed: bytes
	_uncompressed: bytes
	
	def __init__(self, compressed: bytes) -> None:
		super().__init__()
		
		self.compressed = compressed
	
	def __eq__(self, other) -> bool:
		return isinstance(other, ICNSStylePackbits) and self.compressed == other.compressed
	
	def __hash__(self) -> int:
		return hash(self.compressed)
	
	def __str__(self) -> str:
		return f"<{type(self).__qualname__}: {len(self.compressed)} bytes compressed>"
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}(compressed={self.compressed!r})"
	
	@property
	def uncompressed(self) -> bytes:
		try:
			return self._uncompressed
		except AttributeError:
			self._uncompressed = b"".join(_decompress_icns_style_packbits(_KSElement.IcnsStylePackbits.from_bytes(self.compressed).chunks))
			return self._uncompressed


@dataclasses.dataclass(frozen=True)
class IconRGB(Icon):
	rgb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: typing.Union[_KSElement.IconRgbData, _KSElement.IconRgbZeroPrefixedData]) -> "IconRGB":
		if isinstance(struct, _KSElement.IconRgbZeroPrefixedData):
			struct = struct.icon
		
		return cls(struct.width, struct.height, 1, ICNSStylePackbits(struct.data.compressed_data))


@dataclasses.dataclass(frozen=True)
class Icon8BitMask(Icon):
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8MaskData) -> "Icon8BitMask":
		return cls(struct.width, struct.height, 1, struct.mask)


@dataclasses.dataclass(frozen=True)
class IconARGB(Icon):
	argb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconArgbData) -> "IconARGB":
		return cls(struct.width, struct.height, 1, ICNSStylePackbits(struct.compressed_data.compressed_data))


@dataclasses.dataclass(frozen=True)
class IconPNGOrJPEG2000(Icon):
	data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconPngJp2Data) -> "IconPNGOrJPEG2000":
		return cls(struct.point_width, struct.point_height, struct.scale, struct.png_or_jp2_data)
	
	@property
	def is_png(self) -> bool:
		return self.data.startswith(b"\x89PNG\r\n\x1a\n")
	
	@property
	def is_jpeg_2000(self) -> bool:
		return self.data.startswith(b"\x00\x00\x00\x0cjP  \r\n\x87\n")
