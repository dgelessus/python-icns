import abc
import collections
import dataclasses
import io
import os
import typing

import PIL.Image
import PIL.ImageChops

from . import palettes
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
	elements: "collections.OrderedDict[bytes, IconFamilyElement]"
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconFamilyData) -> "IconFamily":
		elements: "collections.OrderedDict[bytes, IconFamilyElement]" = collections.OrderedDict()
		
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
	def from_file(cls, path: typing.Union[str, bytes, os.PathLike]) -> "IconFamily":
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
class IconBase(ParsedElement, metaclass=abc.ABCMeta):
	point_width: int
	point_height: int
	scale: int
	
	@property
	def pixel_width(self) -> int:
		return self.point_width * self.scale
	
	@property
	def pixel_height(self) -> int:
		return self.point_height * self.scale


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class IconWithoutMask(IconBase, metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class IconWithMask(IconBase, metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def to_pil_image(self) -> PIL.Image.Image:
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class Mask(IconBase, metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def to_pil_image(self) -> PIL.Image.Image:
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class Icon1BitAndMask(IconWithMask):
	icon_data: bytes
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX1AndMaskData) -> "Icon1BitAndMask":
		return cls(struct.width, struct.height, 1, struct.icon, struct.mask)
	
	def to_pil_image(self) -> PIL.Image.Image:
		image = PIL.Image.frombytes("1", (self.pixel_width, self.pixel_height), self.icon_data)
		# In Macintosh monochrome bitmaps,
		# 0 is white and 1 is black,
		# but Pillow interprets 0 as black and 1 as white.
		# To fix this,
		# invert the image after reading.
		image = PIL.ImageChops.invert(image)
		mask = PIL.Image.frombytes("1", (self.pixel_width, self.pixel_height), self.mask_data)
		# Pillow doesn't support directly adding an alpha channel to a 1-bit image,
		# so convert it to 8-bit first.
		image_with_alpha = image.convert("L")
		image_with_alpha.putalpha(mask)
		return image_with_alpha


def _add_mask_to_palette_image(image: PIL.Image.Image, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
	if mask is None:
		return image
	else:
		# Adding an alpha channel/mask to a palette image doesn't work properly (as of Pillow 7.2.0) -
		# doing so correctly changes the mode from "P" to "PA",
		# but also resets the palette to default,
		# and doesn't actually add any transparency.
		# As a workaround,
		# convert the image to RGB before adding the alpha channel/mask.
		image_with_alpha = image.convert("RGB")
		image_with_alpha.putalpha(mask)
		return image_with_alpha


@dataclasses.dataclass(frozen=True)
class Icon4Bit(IconWithoutMask):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX4Data) -> "Icon4Bit":
		return cls(struct.width, struct.height, 1, struct.icon)
	
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		# Pillow doesn't support loading raw bitmaps with 4 bits per pixel
		# (at least not through any public API).
		# As a workaround,
		# convert the data to 8 bits per pixel by splitting each byte into two.
		# (This can probably be done more efficiently with numpy,
		# but the bitmaps are so small that it's probably not worth adding the extra dependency just for this.)
		data_8_bit = bytearray()
		for byte in self.icon_data:
			data_8_bit.append(byte >> 4 & 0xf)
			data_8_bit.append(byte >> 0 & 0xf)
		
		image = PIL.Image.frombytes("L", (self.pixel_width, self.pixel_height), bytes(data_8_bit))
		image.putpalette(palettes.MACINTOSH_4_BIT_PALETTE)
		return _add_mask_to_palette_image(image, mask)


@dataclasses.dataclass(frozen=True)
class Icon8Bit(IconWithoutMask):
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8Data) -> "Icon8Bit":
		return cls(struct.width, struct.height, 1, struct.icon)
	
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		image = PIL.Image.frombytes("L", (self.pixel_width, self.pixel_height), self.icon_data)
		image.putpalette(palettes.MACINTOSH_8_BIT_PALETTE)
		return _add_mask_to_palette_image(image, mask)


class ICNSStylePackbits(object):
	compressed: bytes
	_uncompressed: bytes
	
	def __init__(self, compressed: bytes) -> None:
		super().__init__()
		
		self.compressed = compressed
	
	def __eq__(self, other: object) -> bool:
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
class IconRGB(IconWithoutMask):
	rgb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: typing.Union[_KSElement.IconRgbData, _KSElement.IconRgbZeroPrefixedData]) -> "IconRGB":
		if isinstance(struct, _KSElement.IconRgbZeroPrefixedData):
			struct = struct.icon
		
		return cls(struct.width, struct.height, 1, ICNSStylePackbits(struct.compressed_data.compressed_data))
	
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		rgb_data = self.rgb_data.uncompressed
		channel_length = self.pixel_width * self.pixel_height
		
		r_data = rgb_data[0:channel_length]
		g_data = rgb_data[channel_length:2*channel_length]
		b_data = rgb_data[2*channel_length:3*channel_length]
		
		size = (self.pixel_width, self.pixel_height)
		
		r_image = PIL.Image.frombytes("L", size, r_data)
		g_image = PIL.Image.frombytes("L", size, g_data)
		b_image = PIL.Image.frombytes("L", size, b_data)
		
		if mask is None:
			return PIL.Image.merge("RGB", (r_image, g_image, b_image))
		else:
			return PIL.Image.merge("RGBA", (r_image, g_image, b_image, mask))


@dataclasses.dataclass(frozen=True)
class Icon8BitMask(Mask):
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8MaskData) -> "Icon8BitMask":
		return cls(struct.width, struct.height, 1, struct.mask)
	
	def to_pil_image(self) -> PIL.Image.Image:
		return PIL.Image.frombytes("L", (self.pixel_width, self.pixel_height), self.mask_data)


@dataclasses.dataclass(frozen=True)
class IconARGB(IconWithMask):
	argb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconArgbData) -> "IconARGB":
		return cls(struct.width, struct.height, 1, ICNSStylePackbits(struct.compressed_data.compressed_data))
	
	def to_pil_image(self) -> PIL.Image.Image:
		argb_data = self.argb_data.uncompressed
		channel_length = self.pixel_width * self.pixel_height
		
		a_data = argb_data[0:channel_length]
		r_data = argb_data[channel_length:2*channel_length]
		g_data = argb_data[2*channel_length:3*channel_length]
		b_data = argb_data[3*channel_length:4*channel_length]
		
		size = (self.pixel_width, self.pixel_height)
		
		a_image = PIL.Image.frombytes("L", size, a_data)
		r_image = PIL.Image.frombytes("L", size, r_data)
		g_image = PIL.Image.frombytes("L", size, g_data)
		b_image = PIL.Image.frombytes("L", size, b_data)
		
		return PIL.Image.merge("RGBA", (r_image, g_image, b_image, a_image))


@dataclasses.dataclass(frozen=True)
class IconPNGOrJPEG2000(IconWithMask):
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
	
	def to_pil_image(self) -> PIL.Image.Image:
		return PIL.Image.open(io.BytesIO(self.data))
