# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

from . import bytes_with_io
class Icns(KaitaiStruct):
    """Icon image format used by Mac OS 8.5 and later,
    including all versions of Mac OS X/macOS.
    This is the Mac equivalent of the Windows ICO format.
    
    An ICNS file stores an *icon family*:
    a collection of images with visually the same content,
    but at different resolutions and color depths.
    When the system renders an icon on screen,
    it chooses the most optimal format from the icon family to display to the user,
    depending on the icon's displayed size and the capabilities of the display hardware.
    
    An icon family in an ICNS file can also contain other nested icon families.
    This feature is sometimes used to represent different states or visual variants of the same icon,
    such as an opened, selected or dark mode version.
    
    Each icon in an icon family is identified by a four-byte type code,
    which also indicates the image data format and resolution.
    Supported formats include PNG and JPEG 2000 (for larger sizes and modern systems)
    and multiple raw bitmap formats with varying resolution, color depth, and transparency support
    (for smaller sizes and/or compatibility with older systems).
    
    ICNS data can be stored either as a standalone file,
    or as a resource with type code `'icns'` in a resource fork.
    The latter was especially common on Classic Mac OS and for Carbon applications,
    and is still used (as of macOS 10.14) by the Finder to store custom file and folder icons set by the user.
    
    .. seealso::
       <OSServices/IconStorage.h>
    
    
    .. seealso::
       <OSServices/IconStorage.r>
    
    
    .. seealso::
       <HIServices/Icons.r>
    
    
    .. seealso::
       libicns SourceForge project - https://sourceforge.net/p/icns/
    
    
    .. seealso::
       Python Pillow ICNS plugin code - https://github.com/python-pillow/Pillow/blob/master/src/PIL/IcnsImagePlugin.py
    
    
    .. seealso::
       Information about 'icns' resources in resource forks - https://www.macdisk.com/maciconen.php#icns
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.root_element = Icns.IconFamilyElement(self._io, self, self._root)
        _ = self.root_element
        if not _.header.type.as_enum == Icns.IconFamilyElement.Header.Type.main_family:
            raise kaitaistruct.ValidationExprError(self.root_element, self._io, u"/seq/0")

    class IconFamilyElement(KaitaiStruct):
        """A single element in an icon family.
        
        It is normally safe to ignore elements with an unrecognized type code or unparseable data when reading -
        they are most likely new icon types/resolutions, icon family variants, or metadata introduced in a newer system version.
        However, when modifying and writing an icon family,
        such elements should be stripped out,
        to avoid leaving outdated information in the icon family that could be used by newer systems.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.header = Icns.IconFamilyElement.Header(self._io, self, self._root)
            self._raw_data_with_io = self._io.read_bytes(self.header.len_data)
            _io__raw_data_with_io = KaitaiStream(BytesIO(self._raw_data_with_io))
            self.data_with_io = bytes_with_io.BytesWithIo(_io__raw_data_with_io)

        class InfoDictionaryData(KaitaiStruct):
            """The element data for an info dictionary."""
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.archived_data = self._io.read_bytes_full()


        class IconRgbZeroPrefixedData(KaitaiStruct):
            """A variant of icon_rgb_data that has four extra zero bytes preceding the compressed RGB data.
            This variant is only used by the 'it32' (icon_128x128_rgb) icon type.
            """
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.zero_prefix = self._io.read_bytes(4)
                if not self.zero_prefix == b"\x00\x00\x00\x00":
                    raise kaitaistruct.ValidationNotEqualError(b"\x00\x00\x00\x00", self.zero_prefix, self._io, u"/types/icon_family_element/types/icon_rgb_zero_prefixed_data/seq/0")
                self.icon = Icns.IconFamilyElement.IconRgbData(self.width, self.height, self._io, self, self._root)


        class IconComposerVersionData(KaitaiStruct):
            """The element data for an Icon Composer version number."""
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.version = self._io.read_f4be()


        class IcnsStylePackbits(KaitaiStruct):
            """A run-length encoding compression scheme similar to (but not the same as) PackBits.
            Used in the RGB and ARGB bitmap icon types.
            """
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.compressed_data_with_io = bytes_with_io.BytesWithIo(self._io)

            class Chunk(KaitaiStruct):
                """A single chunk of compressed data.
                Each chunk stores either a sequence of literal bytes,
                or a single byte that is repeated a certain number of times.
                """
                def __init__(self, _io, _parent=None, _root=None):
                    self._io = _io
                    self._parent = _parent
                    self._root = _root if _root else self
                    self._read()

                def _read(self):
                    self.tag = self._io.read_u1()
                    if not (self.is_repeat):
                        self.literal_data = self._io.read_bytes((self.tag + 1))

                    if self.is_repeat:
                        self.repeated_byte = self._io.read_u1()


                @property
                def is_repeat(self):
                    """If true, this is a repeat chunk.
                    If false, this is a literal chunk.
                    """
                    if hasattr(self, '_m_is_repeat'):
                        return self._m_is_repeat if hasattr(self, '_m_is_repeat') else None

                    self._m_is_repeat = self.tag >= 128
                    return self._m_is_repeat if hasattr(self, '_m_is_repeat') else None

                @property
                def len_literal_data(self):
                    """If this is a literal chunk,
                    the number of literal bytes stored in the chunk.
                    """
                    if hasattr(self, '_m_len_literal_data'):
                        return self._m_len_literal_data if hasattr(self, '_m_len_literal_data') else None

                    if not (self.is_repeat):
                        self._m_len_literal_data = (self.tag + 1)

                    return self._m_len_literal_data if hasattr(self, '_m_len_literal_data') else None

                @property
                def repeat_count(self):
                    """If this is a repeat chunk,
                    the number of times the stored byte should be repeated in the output.
                    """
                    if hasattr(self, '_m_repeat_count'):
                        return self._m_repeat_count if hasattr(self, '_m_repeat_count') else None

                    if self.is_repeat:
                        self._m_repeat_count = (self.tag - 125)

                    return self._m_repeat_count if hasattr(self, '_m_repeat_count') else None


            @property
            def compressed_data(self):
                """The raw compressed data."""
                if hasattr(self, '_m_compressed_data'):
                    return self._m_compressed_data if hasattr(self, '_m_compressed_data') else None

                self._m_compressed_data = self.compressed_data_with_io.data
                return self._m_compressed_data if hasattr(self, '_m_compressed_data') else None

            @property
            def chunks(self):
                """The compressed data parsed into chunks."""
                if hasattr(self, '_m_chunks'):
                    return self._m_chunks if hasattr(self, '_m_chunks') else None

                _pos = self._io.pos()
                self._io.seek(0)
                self._m_chunks = []
                i = 0
                while not self._io.is_eof():
                    self._m_chunks.append(Icns.IconFamilyElement.IcnsStylePackbits.Chunk(self._io, self, self._root))
                    i += 1

                self._io.seek(_pos)
                return self._m_chunks if hasattr(self, '_m_chunks') else None


        class TableOfContentsData(KaitaiStruct):
            """The element data for a table of contents."""
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.element_headers = []
                i = 0
                while not self._io.is_eof():
                    self.element_headers.append(Icns.IconFamilyElement.Header(self._io, self, self._root))
                    i += 1



        class IconX8MaskData(KaitaiStruct):
            """The data for an 8-bit mask,
            to be used together with one of the maskless bitmap icons of the same size in the same family.
            """
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.mask = self._io.read_bytes((self.width * self.height))


        class IconX1AndMaskData(KaitaiStruct):
            """The data for a 1-bit monochrome bitmap icon with a 1-bit mask."""
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.icon = self._io.read_bytes((self.width * self.height) // 8)
                self.mask = self._io.read_bytes((self.width * self.height) // 8)


        class IconX4Data(KaitaiStruct):
            """The data for a 4-bit color bitmap icon.
            These icons do not contain a mask and instead use the mask from one of the other elements in the same family
            (the 8-bit mask element if possible,
            otherwise the 1-bit mask from the 1-bit icon).
            """
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.icon = self._io.read_bytes((self.width * self.height) // 2)


        class IconPngJp2Data(KaitaiStruct):
            """The data for a PNG or JPEG 2000 icon.
            Mac OS X 10.5 only supports the JPEG 2000 format here;
            Mac OS X 10.6 and later support both PNG and JPEG 2000.
            
            As of Mac OS X 10.7,
            practically all system icons use PNG instead of JPEG 2000,
            and the developer tools (Icon Composer and `iconutil`) always output PNG data.
            The JPEG 2000 format is almost never used anymore here.
            """
            def __init__(self, point_width, point_height, scale, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.point_width = point_width
                self.point_height = point_height
                self.scale = scale
                self._read()

            def _read(self):
                self.png_or_jp2_data = self._io.read_bytes_full()

            @property
            def pixel_width(self):
                """The width of the icon in pixels,
                calculated based on the width in points and the scale.
                """
                if hasattr(self, '_m_pixel_width'):
                    return self._m_pixel_width if hasattr(self, '_m_pixel_width') else None

                self._m_pixel_width = (self.point_width * self.scale)
                return self._m_pixel_width if hasattr(self, '_m_pixel_width') else None

            @property
            def png_signature(self):
                """The PNG format's signature."""
                if hasattr(self, '_m_png_signature'):
                    return self._m_png_signature if hasattr(self, '_m_png_signature') else None

                self._m_png_signature = b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
                return self._m_png_signature if hasattr(self, '_m_png_signature') else None

            @property
            def jp2_signature(self):
                """The JPEG 2000 format's signature."""
                if hasattr(self, '_m_jp2_signature'):
                    return self._m_jp2_signature if hasattr(self, '_m_jp2_signature') else None

                self._m_jp2_signature = b"\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A"
                return self._m_jp2_signature if hasattr(self, '_m_jp2_signature') else None

            @property
            def jp2_signature_check(self):
                """Internal helper instance used to check if the data starts with the JPEG 2000 signature."""
                if hasattr(self, '_m_jp2_signature_check'):
                    return self._m_jp2_signature_check if hasattr(self, '_m_jp2_signature_check') else None

                _pos = self._io.pos()
                self._io.seek(0)
                self._m_jp2_signature_check = self._io.read_bytes(len(self.jp2_signature))
                self._io.seek(_pos)
                return self._m_jp2_signature_check if hasattr(self, '_m_jp2_signature_check') else None

            @property
            def pixel_height(self):
                """The height of the icon in pixels,
                calculated based on the height in points and the scale.
                """
                if hasattr(self, '_m_pixel_height'):
                    return self._m_pixel_height if hasattr(self, '_m_pixel_height') else None

                self._m_pixel_height = (self.point_height * self.scale)
                return self._m_pixel_height if hasattr(self, '_m_pixel_height') else None

            @property
            def is_jp2(self):
                """Whether the data appears to be in JPEG 2000 format (based on its signature)."""
                if hasattr(self, '_m_is_jp2'):
                    return self._m_is_jp2 if hasattr(self, '_m_is_jp2') else None

                self._m_is_jp2 = self.jp2_signature_check == self.jp2_signature
                return self._m_is_jp2 if hasattr(self, '_m_is_jp2') else None

            @property
            def png_signature_check(self):
                """Internal helper instance used to check if the data starts with the PNG signature."""
                if hasattr(self, '_m_png_signature_check'):
                    return self._m_png_signature_check if hasattr(self, '_m_png_signature_check') else None

                _pos = self._io.pos()
                self._io.seek(0)
                self._m_png_signature_check = self._io.read_bytes(len(self.png_signature))
                self._io.seek(_pos)
                return self._m_png_signature_check if hasattr(self, '_m_png_signature_check') else None

            @property
            def is_png(self):
                """Whether the data appears to be in PNG format (based on its signature)."""
                if hasattr(self, '_m_is_png'):
                    return self._m_is_png if hasattr(self, '_m_is_png') else None

                self._m_is_png = self.png_signature_check == self.png_signature
                return self._m_is_png if hasattr(self, '_m_is_png') else None


        class IconArgbData(KaitaiStruct):
            """The data for a 32-bit ARGB bitmap icon."""
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.signature = self._io.read_bytes(4)
                if not self.signature == b"\x41\x52\x47\x42":
                    raise kaitaistruct.ValidationNotEqualError(b"\x41\x52\x47\x42", self.signature, self._io, u"/types/icon_family_element/types/icon_argb_data/seq/0")
                self.compressed_data = Icns.IconFamilyElement.IcnsStylePackbits(self._io, self, self._root)


        class IconRgbData(KaitaiStruct):
            """The data for a 24-bit RGB bitmap icon.
            These icons do not contain a mask and instead use the mask from one of the other elements in the same family
            (the 8-bit mask element if possible,
            otherwise the 1-bit mask from the 1-bit icon).
            """
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.compressed_data = Icns.IconFamilyElement.IcnsStylePackbits(self._io, self, self._root)


        class IconFamilyData(KaitaiStruct):
            """The element data for an icon family."""
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.elements = []
                i = 0
                while not self._io.is_eof():
                    self.elements.append(Icns.IconFamilyElement(self._io, self, self._root))
                    i += 1



        class Header(KaitaiStruct):
            """An icon family element's header,
            storing the type code and length.
            """

            class Type(Enum):
                icon_32x32x1_with_mask = 1229147683
                table_of_contents = 1414480672
                drop_variant_family = 1685221232
                icon_48x48x8_mask = 1748528491
                icon_16x16_argb = 1768108084
                icon_32x32_argb = 1768108085
                icon_128x128_png_jp2 = 1768108087
                icon_256x256_png_jp2 = 1768108088
                icon_512x512_png_jp2 = 1768108089
                icon_512x512_at_2x_png_jp2 = 1768108336
                icon_16x16_at_2x_png_jp2 = 1768108337
                icon_32x32_at_2x_png_jp2 = 1768108338
                icon_128x128_at_2x_png_jp2 = 1768108339
                icon_256x256_at_2x_png_jp2 = 1768108340
                icon_48x48x1_with_mask = 1768122403
                icon_48x48x4 = 1768122420
                icon_48x48x8 = 1768122424
                icon_32x32x4 = 1768123444
                icon_32x32x8 = 1768123448
                icon_16x12x1_with_mask = 1768123683
                icon_16x12x4 = 1768123700
                icon_16x12x8 = 1768123704
                icon_composer_version = 1768123990
                main_family = 1768124019
                icon_16x16_png_jp2 = 1768124468
                icon_32x32_png_jp2 = 1768124469
                icon_64x64_png_jp2 = 1768124470
                icon_16x16x1_with_mask = 1768125219
                icon_16x16x4 = 1768125236
                icon_16x16x8 = 1768125240
                icon_18x18_at_2x_png_jp2 = 1768125250
                icon_18x18_argb = 1768125282
                icon_48x48_rgb = 1768436530
                icon_32x32_rgb = 1768698674
                info_dictionary = 1768842863
                icon_16x16_rgb = 1769157426
                icon_128x128_rgb = 1769222962
                icon_32x32x8_mask = 1815637355
                open_drop_variant_family = 1868853872
                open_variant_family = 1869636974
                rollover_variant_family = 1870030194
                icon_16x16x8_mask = 1933077867
                sbpp_variant_family = 1935831152
                sidebar_variant_family = 1935832176
                selected_variant_family = 1936483188
                icon_128x128x8_mask = 1949855083
                tile_variant_family = 1953066085
                dark_mode_variant_family = 4258869160
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self._raw_type = self._io.read_bytes(4)
                _io__raw_type = KaitaiStream(BytesIO(self._raw_type))
                self.type = Icns.IconFamilyElement.Header.TypeCode(_io__raw_type, self, self._root)
                self.len_element = self._io.read_u4be()

            class TypeCode(KaitaiStruct):
                """A four-character type code."""
                def __init__(self, _io, _parent=None, _root=None):
                    self._io = _io
                    self._parent = _parent
                    self._root = _root if _root else self
                    self._read()

                def _read(self):
                    self.as_bytes = self._io.read_bytes_full()

                @property
                def as_enum(self):
                    """The type code as an integer-based enum."""
                    if hasattr(self, '_m_as_enum'):
                        return self._m_as_enum if hasattr(self, '_m_as_enum') else None

                    _pos = self._io.pos()
                    self._io.seek(0)
                    self._m_as_enum = KaitaiStream.resolve_enum(Icns.IconFamilyElement.Header.Type, self._io.read_u4be())
                    self._io.seek(_pos)
                    return self._m_as_enum if hasattr(self, '_m_as_enum') else None


            @property
            def len_data(self):
                """The length of the data stored in the element.
                This is the length of the entire element minus the length of the header.
                """
                if hasattr(self, '_m_len_data'):
                    return self._m_len_data if hasattr(self, '_m_len_data') else None

                self._m_len_data = (self.len_element - 8)
                return self._m_len_data if hasattr(self, '_m_len_data') else None


        class IconX8Data(KaitaiStruct):
            """The data for an 8-bit color bitmap icon.
            These icons do not contain a mask and instead use the mask from one of the other elements in the same family
            (the 8-bit mask element if possible,
            otherwise the 1-bit mask from the 1-bit icon).
            """
            def __init__(self, width, height, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self.width = width
                self.height = height
                self._read()

            def _read(self):
                self.icon = self._io.read_bytes((self.width * self.height))


        @property
        def data(self):
            """The raw data stored in the element."""
            if hasattr(self, '_m_data'):
                return self._m_data if hasattr(self, '_m_data') else None

            self._m_data = self.data_with_io.data
            return self._m_data if hasattr(self, '_m_data') else None

        @property
        def data_parsed(self):
            """The data stored in the element,
            parsed based on the type code in the header.
            """
            if hasattr(self, '_m_data_parsed'):
                return self._m_data_parsed if hasattr(self, '_m_data_parsed') else None

            io = self.data_with_io._io
            _pos = io.pos()
            io.seek(0)
            _on = self.header.type.as_enum
            if _on == Icns.IconFamilyElement.Header.Type.icon_48x48x4:
                self._m_data_parsed = Icns.IconFamilyElement.IconX4Data(48, 48, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x12x8:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8Data(16, 12, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_128x128x8_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8MaskData(128, 128, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32x1_with_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX1AndMaskData(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_48x48x8_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8MaskData(48, 48, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_48x48_rgb:
                self._m_data_parsed = Icns.IconFamilyElement.IconRgbData(48, 48, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x12x1_with_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX1AndMaskData(16, 12, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.table_of_contents:
                self._m_data_parsed = Icns.IconFamilyElement.TableOfContentsData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_256x256_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(256, 256, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(16, 16, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32_argb:
                self._m_data_parsed = Icns.IconFamilyElement.IconArgbData(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16x1_with_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX1AndMaskData(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.selected_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_128x128_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(128, 128, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_18x18_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(18, 18, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_512x512_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(512, 512, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16_rgb:
                self._m_data_parsed = Icns.IconFamilyElement.IconRgbData(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x12x4:
                self._m_data_parsed = Icns.IconFamilyElement.IconX4Data(16, 12, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.sbpp_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.open_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(32, 32, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.sidebar_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_256x256_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(256, 256, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32x4:
                self._m_data_parsed = Icns.IconFamilyElement.IconX4Data(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.info_dictionary:
                self._m_data_parsed = Icns.IconFamilyElement.InfoDictionaryData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16x4:
                self._m_data_parsed = Icns.IconFamilyElement.IconX4Data(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_128x128_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(128, 128, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(16, 16, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_48x48x8:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8Data(48, 48, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16x8:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8Data(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32_rgb:
                self._m_data_parsed = Icns.IconFamilyElement.IconRgbData(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32x8:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8Data(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.rollover_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16x8_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8MaskData(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_64x64_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(64, 64, 1, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_18x18_argb:
                self._m_data_parsed = Icns.IconFamilyElement.IconArgbData(18, 18, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32x8_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX8MaskData(32, 32, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_16x16_argb:
                self._m_data_parsed = Icns.IconFamilyElement.IconArgbData(16, 16, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_512x512_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(512, 512, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.open_drop_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_128x128_rgb:
                self._m_data_parsed = Icns.IconFamilyElement.IconRgbZeroPrefixedData(128, 128, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_48x48x1_with_mask:
                self._m_data_parsed = Icns.IconFamilyElement.IconX1AndMaskData(48, 48, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_composer_version:
                self._m_data_parsed = Icns.IconFamilyElement.IconComposerVersionData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.drop_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.dark_mode_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.icon_32x32_at_2x_png_jp2:
                self._m_data_parsed = Icns.IconFamilyElement.IconPngJp2Data(32, 32, 2, io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.main_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            elif _on == Icns.IconFamilyElement.Header.Type.tile_variant_family:
                self._m_data_parsed = Icns.IconFamilyElement.IconFamilyData(io, self, self._root)
            else:
                self._m_data_parsed = bytes_with_io.BytesWithIo(io)
            io.seek(_pos)
            _ = self.data_parsed
            if not self._io.is_eof():
                raise kaitaistruct.ValidationExprError(self.data_parsed, self._io, u"/types/icon_family_element/instances/data_parsed")
            return self._m_data_parsed if hasattr(self, '_m_data_parsed') else None



