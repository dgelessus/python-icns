import collections
import dataclasses
import os
import typing

from ._kaitai_struct import bytes_with_io
from ._kaitai_struct import icns


_KSElement = icns.Icns.IconFamilyElement


def _decompress_icns_style_packbits(chunks: typing.Iterable[_KSElement.IcnsStylePackbits.Chunk]) -> typing.Iterable[bytes]:
	for chunk in chunks:
		if chunk.is_repeat:
			yield bytes([chunk.repeated_byte]) * chunk.repeat_count
		else:
			yield chunk.literal_data


class IconFamilyElement(object):
	pass


@dataclasses.dataclass()
class IconFamily(IconFamilyElement):
	elements: typing.OrderedDict[bytes, IconFamilyElement]
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconFamilyData) -> "IconFamily":
		elements: typing.OrderedDict[bytes, IconFamilyElement] = collections.OrderedDict()
		
		for element_struct in struct.elements:
			element: IconFamilyElement
			element_data_struct = element_struct.data_parsed
			if isinstance(element_data_struct, _KSElement.IconFamilyData):
				element = IconFamily.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.TableOfContentsData):
				element = TableOfContents.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconComposerVersionData):
				element = IconComposerVersion.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.InfoDictionaryData):
				element = InfoDictionary.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX1AndMaskData):
				element = Icon1BitAndMask.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX4Data):
				element = Icon4Bit.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconX8Data):
				element = Icon8Bit.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconRgbData):
				element = IconRGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconRgbMaskData):
				element = IconRGBMask.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconRgbZeroPrefixedData):
				element = IconRGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconArgbData):
				element = IconARGB.from_ks(element_data_struct)
			elif isinstance(element_data_struct, _KSElement.IconPngJp2Data):
				element = IconPNGOrJPEG2000.from_ks(element_data_struct)
			else:
				raise AssertionError(f"Unhandled KS element data type: {type(element_data_struct)}")
			
			elements[element_struct.header.type.as_bytes] = element
		
		return cls(elements)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "IconFamily":
		return cls.from_ks(icns.Icns.from_io(stream).root_element.data_parsed)
	
	@classmethod
	def from_file(cls, path: typing.Union[str, bytes, os.PathLike]):
		with open(path, "rb") as f:
			return cls.from_stream(f)


@dataclasses.dataclass()
class TableOfContents(IconFamilyElement):
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


@dataclasses.dataclass()
class IconComposerVersion(IconFamilyElement):
	version: float
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconComposerVersionData) -> "IconComposerVersion":
		return cls(struct.version)


@dataclasses.dataclass()
class InfoDictionary(IconFamilyElement):
	archived_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.InfoDictionaryData) -> "InfoDictionary":
		return cls(struct.archived_data)


@dataclasses.dataclass()
class Icon(IconFamilyElement):
	point_width: int
	point_height: int
	scale: int
	
	@property
	def pixel_width(self) -> int:
		return self.point_width * self.scale
	
	@property
	def pixel_height(self) -> int:
		return self.point_height * self.scale


@dataclasses.dataclass()
class Icon1BitAndMask(Icon):
	icon_data: bytes
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX1AndMaskData) -> "Icon1BitAndMask":
		return cls(struct.width, struct.height, 1, struct.icon, struct.mask)


@dataclasses.dataclass()
class Icon4Bit(Icon):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX4Data) -> "Icon4Bit":
		return cls(struct.width, struct.height, 1, struct.icon)


@dataclasses.dataclass()
class Icon8Bit(Icon):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8Data) -> "Icon8Bit":
		return cls(struct.width, struct.height, 1, struct.icon)


@dataclasses.dataclass()
class IconRGB(Icon):
	rgb_data: bytes
	
	@classmethod
	def from_ks(cls, struct: typing.Union[_KSElement.IconRgbData, _KSElement.IconRgbZeroPrefixedData]) -> "IconRGB":
		if isinstance(struct, _KSElement.IconRgbZeroPrefixedData):
			struct = struct.icon
		
		data = b"".join(_decompress_icns_style_packbits(struct.data.chunks))
		return cls(struct.width, struct.height, 1, data)


@dataclasses.dataclass()
class IconRGBMask(Icon):
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconRgbMaskData) -> "IconRGBMask":
		return cls(struct.width, struct.height, 1, struct.mask)


@dataclasses.dataclass()
class IconARGB(Icon):
	argb_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconArgbData) -> "IconARGB":
		data = b"".join(_decompress_icns_style_packbits(struct.compressed_data.chunks))
		return cls(struct.width, struct.height, 1, data)


@dataclasses.dataclass()
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
