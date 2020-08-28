import abc
import collections
import dataclasses
import io
import os
import typing

import PIL.Image
import PIL.ImageChops

from . import element_types
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
	"""An element inside an icon family.
	
	The element's four-byte type code is stored as :class:`bytes` in :attr:`type`,
	and the raw data is stored in :attr:`data`.
	If the type code is recognized and supported by this library,
	additional information about the type is available in :attr:`known_type`,
	and a parsed form of the element's data can be accessed through :attr:`parsed`.
	If the element's type is not recognized,
	:attr:`known_type` is ``None``,
	and :attr:`parsed` cannot be accessed.
	"""
	
	type: bytes
	known_type: typing.Optional[element_types.KnownElementType]
	data: bytes
	_struct: _KSElement
	_parsed: "ParsedElement"
	
	def __init__(self, type: bytes, data: bytes, *, _struct: _KSElement) -> None:
		super().__init__()
		
		self.type = type
		self.known_type = element_types.KnownElementType.by_typecode.get(self.type)
		self.data = data
		self._struct = _struct
	
	@classmethod
	def from_ks(cls, struct: _KSElement) -> "IconFamilyElement":
		return cls(struct.header.type.as_bytes, struct.data, _struct=struct)
	
	@property
	def parsed(self) -> "ParsedElement":
		"""The element's data parsed based on the type code.
		
		.. note::
		
			This attribute is calculated lazily and cached.
			That is,
			accessing this attribute multiple times only parses the data once,
			and the data is not parsed if this attribute is never accessed.
		"""
		
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
	"""Base class for all parsed element data.
	
	There are no generic APIs that are supported on all parsed data objects.
	To operate generically on elements of any type,
	use the unparsed :class:`IconFamilyElement` objects instead.
	"""


class IconFamily(ParsedElement):
	"""The contents of an ICNS image -
	a collection of icons in different resolutions, color depths and data formats,
	as well as possibly metadata and other nested icon families.
	
	This class supports looking up elements by their raw type code,
	or (in the case of icons) by their resolution and data type.
	It also provides methods for looking up the best quality icon for a certain size,
	and for automatically finding and applying masks to icons that don't include an alpha channel.
	"""
	
	elements: "collections.OrderedDict[bytes, IconFamilyElement]"
	elements_by_resolution_and_type: typing.DefaultDict[element_types.Resolution, typing.Dict[element_types.DataType, IconFamilyElement]]
	
	def __init__(self, elements: "collections.OrderedDict[bytes, IconFamilyElement]") -> None:
		super().__init__()
		
		self.elements = elements
		self.elements_by_resolution_and_type = collections.defaultdict(dict)
		for element in self.elements.values():
			if not isinstance(element.known_type, element_types.KnownIconType):
				continue
			
			self.elements_by_resolution_and_type[element.known_type.resolution][element.known_type.data_type] = element
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconFamilyData) -> "IconFamily":
		elements: "collections.OrderedDict[bytes, IconFamilyElement]" = collections.OrderedDict()
		
		for element_struct in struct.elements:
			element = IconFamilyElement.from_ks(element_struct)
			elements[element.type] = element
		
		return cls(elements)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "IconFamily":
		"""Parse an :class:`IconFamily` from an ICNS image stored in the given stream."""
		
		return cls.from_ks(icns.Icns.from_io(stream).root_element.data_parsed)
	
	@classmethod
	def from_file(cls, path: typing.Union[str, bytes, os.PathLike]) -> "IconFamily":
		"""Parse an :class:`IconFamily` from an ICNS image stored at the given path."""
		
		with open(path, "rb") as f:
			return cls.from_stream(f)
	
	def _best_element_for_resolution(self, resolution: element_types.Resolution, ranking: typing.Mapping[element_types.DataType, int]) -> IconFamilyElement:
		"""Internal helper method for looking up the icon family element with the "best" data type for a certain resolution.
		
		:param ranking: A map that contains all data types that may be selected and maps them to a "quality" integer.
		:return: The element in this family that has the data type with the highest "quality" number,
			out of all the data types from the ``ranking`` map that exist in this icon family for the given resolution.
		:raise KeyError: If none of the elements in this family for the given resolution match any of the data types in ``ranking``.
		"""
		
		elements_for_resolution_by_type = self.elements_by_resolution_and_type[resolution]
		available_matching_types = set(ranking).intersection(elements_for_resolution_by_type)
		if not available_matching_types:
			raise KeyError(f"None of the requested types ({ranking.keys()}) are available for resolution {resolution} (available types are {elements_for_resolution_by_type})")
		best_mask_data_type = max(available_matching_types, key=lambda tp: ranking[tp])
		return elements_for_resolution_by_type[best_mask_data_type]
	
	def mask_element_for_resolution(self, resolution: element_types.Resolution) -> IconFamilyElement:
		"""Find a mask element with the given resolution in this family.
		
		If the family contains multiple mask elements for the given resolution,
		the one with the highest quality is returned.
		To match the behavior of Mac OS X/macOS,
		only 8-bit separate mask elements and 1-bit masks from monochrome icon elements are considered,
		with the former being preferred over the latter.
		Masks from ARGB, JPEG 2000 and PNG icons are *not* considered.
		
		The returned element's :attr:`~IconFamilyElement.parsed` attribute will be an instance of either :class:`Mask` (in the case of an 8-bit separate mask) or :class:`IconWithMask` (in the case of a 1-bit mask in a monochrome icon).
		In the latter case,
		the element contains both icon and mask data,
		which must be handled differently than elements that contain only a mask.
		Consider using :func:`mask_image_for_resolution` instead if possible,
		which automatically handles the different possible types and always returns the mask as a :class:`PIL.Image.Image`.
		
		:raise KeyError: If the family contains no mask with the given resolution.
		"""
		
		return self._best_element_for_resolution(resolution, element_types.MASK_TYPE_QUALITIES)
	
	def icon_element_for_resolution(self, resolution: element_types.Resolution) -> IconFamilyElement:
		"""Find an icon element with the given resolution in this family.
		
		If the family contains multiple icon elements for the given resolution,
		the one with the highest quality is returned.
		Icon types with higher color depths are considered higher quality than those with lower color depths,
		and modern data formats are considered higher quality than older ones
		(PNG/JPEG 2000 > ARGB > RGB with separate mask).
		
		The returned element's :attr:`~IconFamilyElement.parsed` attribute will be an instance of either :class:`Icon` (in the case of RGB, 8-bit or 4-bit icons) or :class:`IconWithMask` (in the case of PNG/JPEG 2000, ARGB and monochrome icons).
		In the former case,
		the element doesn't contain an alpha channel,
		so a mask has to be looked up and applied to obtain the proper icon image.
		Consider using :func:`icon_image_for_resolution` instead if possible,
		which automatically handles the different possible types and always returns the icon with an alpha channel as a :class:`PIL.Image.Image`.
		
		:raise KeyError: If the family contains no icon with the given resolution.
		"""
		
		return self._best_element_for_resolution(resolution, element_types.ICON_TYPE_QUALITIES)
	
	def mask_image_for_resolution(self, resolution: element_types.Resolution) -> PIL.Image.Image:
		"""Find a mask with the given resolution in this family and convert it to a :class:`PIL.Image.Image`.
		
		This method doesn't return any information about which element exactly the mask was taken from.
		If you need this information,
		use the lower-level :func:`mask_element_for_resolution` method instead.
		
		:raise KeyError: If the family contains no mask with the given resolution.
		"""
		
		parsed_mask = self.mask_element_for_resolution(resolution).parsed
		if isinstance(parsed_mask, IconWithMask):
			return parsed_mask.to_pil_image().getchannel("A")
		else:
			assert isinstance(parsed_mask, Mask)
			return parsed_mask.to_pil_image()
	
	def icon_image_for_resolution(self, resolution: element_types.Resolution) -> PIL.Image.Image:
		"""Find an with the given resolution in this family and convert it to a :class:`PIL.Image.Image`.
		If the found icon element doesn't have an included alpha channel,
		the best available mask with the same resolution is automatically looked up and applied to the image before returning.
		If no matching mask is found,
		the image is returned without an alpha channel.
		
		This method doesn't return any information about which element exactly the icon and the mask (if any) were taken from.
		If you need this information,
		use the lower-level :func:`mask_element_for_resolution` and :func:`icon_element_for_resolution` methods instead.
		
		:raise KeyError: If the family contains no icon with the given resolution.
		"""
		
		parsed_icon = self.icon_element_for_resolution(resolution).parsed
		if isinstance(parsed_icon, IconWithoutMask):
			try:
				mask_image = self.mask_image_for_resolution(resolution)
			except KeyError:
				mask_image = None
			return parsed_icon.to_pil_image(mask_image)
		else:
			assert isinstance(parsed_icon, IconWithMask)
			return parsed_icon.to_pil_image()


@dataclasses.dataclass(frozen=True)
class TableOfContents(ParsedElement):
	"""An icon family's table of contents.
	
	Contains the header information (type code and element length) for every element in the family
	(except for the `'icnV'` (Icon Composer version) element, if any, and the TOC itself).
	This information can theoretically be used to reduce the amount of data that needs to be read to extract single elements from an icon family,
	by calculating the offsets of the needed elements in the icon family and seeking to them directly,
	instead of reading the entire family sequentially.
	
	The table of contents is only an optimization and is entirely optional -
	icon families don't have to contain a table of contents,
	and if one is present,
	it doesn't need to be used when reading the icon family,
	as the traditional element headers are still present.
	
	This library does not use tables of contents to optimize reads,
	because ICNS images are usually small enough that using the table of contents doesn't provide any significant benefits over reading the entire data upfront.
	"""
	
	@dataclasses.dataclass()
	class Entry(object):
		"""A single entry in the table of contents,
		holding the type code and element length for the corresponding element in the family.
		"""
		
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
	"""An Icon Composer version metadata element,
	written by some versions of Icon Composer.
	
	This metadata has no effect on any other part of the icon family and can be safely ignored when reading and omitted when writing.
	"""
	
	version: float
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconComposerVersionData) -> "IconComposerVersion":
		return cls(struct.version)


@dataclasses.dataclass(frozen=True)
class InfoDictionary(ParsedElement):
	"""A dictionary of metadata, stored as a ``NSDictionary`` serialized using ``NSKeyedArchiver`` into a binary property list (bplist).
	
	This metadata seems to be read and written only by Apple's ``iconutil`` tool.
	It has no effect on any other part of the icon family and can be safely ignored when reading and omitted when writing.
	"""
	
	archived_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.InfoDictionaryData) -> "InfoDictionary":
		return cls(struct.archived_data)


@dataclasses.dataclass(frozen=True)
class IconBase(ParsedElement, metaclass=abc.ABCMeta):
	"""Base class for all parsed elements containing actual image data (icon, mask, or both).
	
	Provides information about the image's resolution in :attr:`resolution`.
	"""
	
	resolution: element_types.Resolution


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class IconWithoutMask(IconBase, metaclass=abc.ABCMeta):
	"""Base class for all parsed elements containing icon image data with no mask."""
	
	@abc.abstractmethod
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		"""Convert the icon image data to a :class:`PIL.Image.Image`.
		
		:param mask: The mask to use as the icon's alpha channel,
			or ``None`` for no alpha channel
			(in which case the returned image is entirely opaque).
		:return: The converted icon.
			The image's exact mode is not specified,
			but if ``mask`` is not ``None``,
			the image will include an alpha channel.
		"""
		
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class IconWithMask(IconBase, metaclass=abc.ABCMeta):
	"""Base class for all parsed elements containing icon image data with a mask/alpha channel."""
	
	@abc.abstractmethod
	def to_pil_image(self) -> PIL.Image.Image:
		"""Convert the icon image data to a :class:`PIL.Image.Image`.
		
		:return: The converted icon.
			The image's exact mode is not specified,
			but it will always include an alpha channel.
		"""
		
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True) # type: ignore # https://github.com/python/mypy/issues/5374
class Mask(IconBase, metaclass=abc.ABCMeta):
	"""Base class for all parsed elements containing only mask data and no icon."""
	
	@abc.abstractmethod
	def to_pil_image(self) -> PIL.Image.Image:
		"""Convert the mask data to a :class:`PIL.Image.Image`.
		
		:return: The converted mask.
			The image's exact mode is not specified,
			but it will always be a single-channel image.
		"""
		
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class Icon1BitAndMask(IconWithMask):
	"""A Classic Mac OS-style 1-bit monochrome bitmap icon with a 1-bit mask."""
	
	icon_data: bytes
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX1AndMaskData) -> "Icon1BitAndMask":
		return cls(element_types.Resolution(struct.width, struct.height, 1), struct.icon, struct.mask)
	
	def to_pil_image(self) -> PIL.Image.Image:
		image = PIL.Image.frombytes("1", self.resolution.pixel_size, self.icon_data)
		# In Macintosh monochrome bitmaps,
		# 0 is white and 1 is black,
		# but Pillow interprets 0 as black and 1 as white.
		# To fix this,
		# invert the image after reading.
		image = PIL.ImageChops.invert(image)
		mask = PIL.Image.frombytes("1", self.resolution.pixel_size, self.mask_data)
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
	"""A Classic Mac OS-style 4-bit color bitmap icon
	(in the system default 4-bit color palette)
	with no mask.
	"""
	
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX4Data) -> "Icon4Bit":
		return cls(element_types.Resolution(struct.width, struct.height, 1), struct.icon)
	
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
		
		image = PIL.Image.frombytes("L", self.resolution.pixel_size, bytes(data_8_bit))
		image.putpalette(palettes.MACINTOSH_4_BIT_PALETTE)
		return _add_mask_to_palette_image(image, mask)


@dataclasses.dataclass(frozen=True)
class Icon8Bit(IconWithoutMask):
	"""A Classic Mac OS-style 8-bit color bitmap icon
	(in the system default 8-bit color palette)
	with no mask.
	"""
	
	icon_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8Data) -> "Icon8Bit":
		return cls(element_types.Resolution(struct.width, struct.height, 1), struct.icon)
	
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		image = PIL.Image.frombytes("L", self.resolution.pixel_size, self.icon_data)
		image.putpalette(palettes.MACINTOSH_8_BIT_PALETTE)
		return _add_mask_to_palette_image(image, mask)


class ICNSStylePackbits(object):
	"""Wrapper for data that is compressed with the ICNS variant of PackBits."""
	
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
		"""The uncompressed data.
		
		.. note::
		
			This attribute is calculated lazily and cached.
			That is,
			accessing this attribute multiple times only decompresses the data once,
			and the data is not decompressed if this attribute is never accessed.
		"""
		
		try:
			return self._uncompressed
		except AttributeError:
			self._uncompressed = b"".join(_decompress_icns_style_packbits(_KSElement.IcnsStylePackbits.from_bytes(self.compressed).chunks))
			return self._uncompressed


@dataclasses.dataclass(frozen=True)
class IconRGB(IconWithoutMask):
	"""A Classic Mac OS-style 24-bit color compressed bitmap icon with no mask."""
	
	rgb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: typing.Union[_KSElement.IconRgbData, _KSElement.IconRgbZeroPrefixedData]) -> "IconRGB":
		if isinstance(struct, _KSElement.IconRgbZeroPrefixedData):
			struct = struct.icon
		
		return cls(element_types.Resolution(struct.width, struct.height, 1), ICNSStylePackbits(struct.compressed_data.compressed_data))
	
	def to_pil_image(self, mask: typing.Optional[PIL.Image.Image]) -> PIL.Image.Image:
		rgb_data = self.rgb_data.uncompressed
		channel_length = self.resolution.pixel_width * self.resolution.pixel_height
		
		r_data = rgb_data[0:channel_length]
		g_data = rgb_data[channel_length:2*channel_length]
		b_data = rgb_data[2*channel_length:3*channel_length]
		
		r_image = PIL.Image.frombytes("L", self.resolution.pixel_size, r_data)
		g_image = PIL.Image.frombytes("L", self.resolution.pixel_size, g_data)
		b_image = PIL.Image.frombytes("L", self.resolution.pixel_size, b_data)
		
		if mask is None:
			return PIL.Image.merge("RGB", (r_image, g_image, b_image))
		else:
			return PIL.Image.merge("RGBA", (r_image, g_image, b_image, mask))


@dataclasses.dataclass(frozen=True)
class Icon8BitMask(Mask):
	"""A Classic Mac OS-style 8-bit mask bitmap,
	for use with bitmap icon elements that don't include a mask.
	"""
	
	mask_data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconX8MaskData) -> "Icon8BitMask":
		return cls(element_types.Resolution(struct.width, struct.height, 1), struct.mask)
	
	def to_pil_image(self) -> PIL.Image.Image:
		return PIL.Image.frombytes("L", self.resolution.pixel_size, self.mask_data)


@dataclasses.dataclass(frozen=True)
class IconARGB(IconWithMask):
	"""A 32-bit color compressed bitmap icon with an included alpha channel."""
	
	argb_data: ICNSStylePackbits
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconArgbData) -> "IconARGB":
		return cls(element_types.Resolution(struct.width, struct.height, 1), ICNSStylePackbits(struct.compressed_data.compressed_data))
	
	def to_pil_image(self) -> PIL.Image.Image:
		argb_data = self.argb_data.uncompressed
		channel_length = self.resolution.pixel_width * self.resolution.pixel_height
		
		a_data = argb_data[0:channel_length]
		r_data = argb_data[channel_length:2*channel_length]
		g_data = argb_data[2*channel_length:3*channel_length]
		b_data = argb_data[3*channel_length:4*channel_length]
		
		a_image = PIL.Image.frombytes("L", self.resolution.pixel_size, a_data)
		r_image = PIL.Image.frombytes("L", self.resolution.pixel_size, r_data)
		g_image = PIL.Image.frombytes("L", self.resolution.pixel_size, g_data)
		b_image = PIL.Image.frombytes("L", self.resolution.pixel_size, b_data)
		
		return PIL.Image.merge("RGBA", (r_image, g_image, b_image, a_image))


@dataclasses.dataclass(frozen=True)
class IconPNGOrJPEG2000(IconWithMask):
	"""An icon in PNG or JPEG 2000 format."""
	
	data: bytes
	
	@classmethod
	def from_ks(cls, struct: _KSElement.IconPngJp2Data) -> "IconPNGOrJPEG2000":
		return cls(element_types.Resolution(struct.point_width, struct.point_height, struct.scale), struct.png_or_jp2_data)
	
	@property
	def is_png(self) -> bool:
		"""Whether the data is in PNG format."""
		
		return self.data.startswith(b"\x89PNG\r\n\x1a\n")
	
	@property
	def is_jpeg_2000(self) -> bool:
		"""Whether the data is in JPEG 2000 format."""
		
		return self.data.startswith(b"\x00\x00\x00\x0cjP  \r\n\x87\n")
	
	def to_pil_image(self) -> PIL.Image.Image:
		return PIL.Image.open(io.BytesIO(self.data))
