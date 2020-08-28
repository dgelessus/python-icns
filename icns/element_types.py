import dataclasses
import collections
import enum
import typing


class DataType(enum.Enum):
	icon_family = enum.auto()
	table_of_contents = enum.auto()
	icon_composer_version = enum.auto()
	info_dictionary = enum.auto()
	icon_1_bit_with_mask = enum.auto()
	icon_4_bit = enum.auto()
	icon_8_bit = enum.auto()
	icon_rgb = enum.auto()
	icon_8_bit_mask = enum.auto()
	icon_argb = enum.auto()
	icon_png_jp2 = enum.auto()


ICON_TYPE_QUALITIES: typing.Mapping[DataType, int] = {
	DataType.icon_1_bit_with_mask: 1,
	DataType.icon_4_bit: 2,
	DataType.icon_8_bit: 3,
	DataType.icon_rgb: 4,
	DataType.icon_argb: 5,
	DataType.icon_png_jp2: 6,
}


MASK_TYPE_QUALITIES: typing.Mapping[DataType, int] = {
	DataType.icon_1_bit_with_mask: 1,
	DataType.icon_8_bit_mask: 2,
}


@dataclasses.dataclass(frozen=True)
class Resolution(object):
	point_width: int
	point_height: int
	scale: int
	
	def __str__(self) -> str:
		rep = f"{self.pixel_width}x{self.pixel_height}"
		if self.scale != 1:
			rep += f" ({self.point_width}x{self.point_height}@{self.scale}x)"
		return rep
	
	@property
	def pixel_width(self) -> int:
		return self.point_width * self.scale
	
	@property
	def pixel_height(self) -> int:
		return self.point_height * self.scale
	
	@property
	def pixel_size(self) -> typing.Tuple[int, int]:
		return self.pixel_width, self.pixel_height


@dataclasses.dataclass(frozen=True)
class KnownElementType(object):
	by_typecode: typing.ClassVar[typing.Dict[bytes, "KnownElementType"]] = {}
	by_data_type: typing.ClassVar[typing.DefaultDict[DataType, typing.Set["KnownElementType"]]] = collections.defaultdict(set)
	
	typecode: bytes
	data_type: DataType
	
	def __post_init__(self) -> None:
		assert self.typecode not in type(self).by_typecode
		type(self).by_typecode[self.typecode] = self
		type(self).by_data_type[self.data_type].add(self)


@dataclasses.dataclass(frozen=True)
class KnownIconType(KnownElementType):
	by_data_type_and_resolution: typing.ClassVar[typing.Dict[typing.Tuple[DataType, Resolution], "KnownIconType"]] = {}
	
	resolution: Resolution
	
	def __post_init__(self) -> None:
		super().__post_init__()
		
		assert (self.data_type, self.resolution) not in self.by_data_type_and_resolution
		self.by_data_type_and_resolution[(self.data_type, self.resolution)] = self


# Icon families
main_family = KnownElementType(b"icns", DataType.icon_family)
tile_variant_family = KnownElementType(b"tile", DataType.icon_family)
rollover_variant_family = KnownElementType(b"over", DataType.icon_family)
drop_variant_family = KnownElementType(b"drop", DataType.icon_family)
open_variant_family = KnownElementType(b"open", DataType.icon_family)
open_drop_variant_family = KnownElementType(b"odrp", DataType.icon_family)
sbpp_variant_family = KnownElementType(b"sbpp", DataType.icon_family)
sidebar_variant_family = KnownElementType(b"sbtp", DataType.icon_family)
selected_variant_family = KnownElementType(b"slct", DataType.icon_family)
dark_mode_variant_family = KnownElementType(b"\xfd\xd9/\xa8", DataType.icon_family)

# Metadata
table_of_contents = KnownElementType(b"TOC ", DataType.table_of_contents)
icon_composer_version = KnownElementType(b"icnV", DataType.table_of_contents)
info_dictionary = KnownElementType(b"info", DataType.info_dictionary)

# Classic bitmap icon images, 16x12 ("mini")
icon_16x12x1_with_mask = KnownIconType(b"icm#", DataType.icon_1_bit_with_mask, Resolution(16, 12, 1))
icon_16x12x4 = KnownIconType(b"icm4", DataType.icon_4_bit, Resolution(16, 12, 1))
icon_16x12x8 = KnownIconType(b"icm8", DataType.icon_8_bit, Resolution(16, 12, 1))

# Classic bitmap icon images, 16x16 ("small")
icon_16x16x1_with_mask = KnownIconType(b"ics#", DataType.icon_1_bit_with_mask, Resolution(16, 16, 1))
icon_16x16x4 = KnownIconType(b"ics4", DataType.icon_4_bit, Resolution(16, 16, 1))
icon_16x16x8 = KnownIconType(b"ics8", DataType.icon_8_bit, Resolution(16, 16, 1))
icon_16x16_rgb = KnownIconType(b"is32", DataType.icon_rgb, Resolution(16, 16, 1))
icon_16x16x8_mask = KnownIconType(b"s8mk", DataType.icon_8_bit_mask, Resolution(16, 16, 1))

# Classic bitmap icon images, 32x32 ("large")
icon_32x32x1_with_mask = KnownIconType(b"ICN#", DataType.icon_1_bit_with_mask, Resolution(32, 32, 1))
icon_32x32x4 = KnownIconType(b"icl4", DataType.icon_4_bit, Resolution(32, 32, 1))
icon_32x32x8 = KnownIconType(b"icl8", DataType.icon_8_bit, Resolution(32, 32, 1))
icon_32x32_rgb = KnownIconType(b"il32", DataType.icon_rgb, Resolution(32, 32, 1))
icon_32x32x8_mask = KnownIconType(b"l8mk", DataType.icon_8_bit_mask, Resolution(32, 32, 1))

# Classic bitmap icon images, 48x48 ("huge")
icon_48x48x1_with_mask = KnownIconType(b"ich#", DataType.icon_1_bit_with_mask, Resolution(48, 48, 1))
icon_48x48x4 = KnownIconType(b"ich4", DataType.icon_4_bit, Resolution(48, 48, 1))
icon_48x48x8 = KnownIconType(b"ich8", DataType.icon_8_bit, Resolution(48, 48, 1))
icon_48x48_rgb = KnownIconType(b"ih32", DataType.icon_rgb, Resolution(48, 48, 1))
icon_48x48x8_mask = KnownIconType(b"h8mk", DataType.icon_8_bit_mask, Resolution(48, 48, 1))

# Classic bitmap icon images, 128x128 ("thumbnail")
icon_128x128_rgb = KnownIconType(b"it32", DataType.icon_rgb, Resolution(128, 128, 1))
icon_128x128x8_mask = KnownIconType(b"t8mk", DataType.icon_8_bit_mask, Resolution(128, 128, 1))

# ARGB bitmap icon images
icon_16x16_argb = KnownIconType(b"ic04", DataType.icon_argb, Resolution(16, 16, 1))
icon_18x18_argb = KnownIconType(b"icsb", DataType.icon_argb, Resolution(18, 18, 1))
icon_32x32_argb = KnownIconType(b"ic05", DataType.icon_argb, Resolution(32, 32, 1))

# PNG/JPEG 2000 icon images, regular scale
icon_16x16_png_jp2 = KnownIconType(b"icp4", DataType.icon_png_jp2, Resolution(16, 16, 1))
icon_32x32_png_jp2 = KnownIconType(b"icp5", DataType.icon_png_jp2, Resolution(32, 32, 1))
icon_64x64_png_jp2 = KnownIconType(b"icp6", DataType.icon_png_jp2, Resolution(64, 64, 1))
icon_128x128_png_jp2 = KnownIconType(b"ic07", DataType.icon_png_jp2, Resolution(128, 128, 1))
icon_256x256_png_jp2 = KnownIconType(b"ic08", DataType.icon_png_jp2, Resolution(256, 256, 1))
icon_512x512_png_jp2 = KnownIconType(b"ic09", DataType.icon_png_jp2, Resolution(512, 512, 1))

# PNG/JPEG 2000 icon images, HiDPI scale (@2x)
icon_16x16_at_2x_png_jp2 = KnownIconType(b"ic11", DataType.icon_png_jp2, Resolution(16, 16, 2))
icon_18x18_at_2x_png_jp2 = KnownIconType(b"icsB", DataType.icon_png_jp2, Resolution(18, 18, 2))
icon_32x32_at_2x_png_jp2 = KnownIconType(b"ic12", DataType.icon_png_jp2, Resolution(32, 32, 2))
icon_128x128_at_2x_png_jp2 = KnownIconType(b"ic13", DataType.icon_png_jp2, Resolution(128, 128, 2))
icon_256x256_at_2x_png_jp2 = KnownIconType(b"ic14", DataType.icon_png_jp2, Resolution(256, 256, 2))
icon_512x512_at_2x_png_jp2 = KnownIconType(b"ic10", DataType.icon_png_jp2, Resolution(512, 512, 2))
