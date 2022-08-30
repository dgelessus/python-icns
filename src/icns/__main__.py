import argparse
import io
import json
import pathlib
import sys
import typing

from . import __version__
from . import api
from . import element_types


def bytes_escape(bs: bytes, *, quote: typing.Optional[str] = None) -> str:
	"""Convert a bytestring to an ASCII string,
	with non-ASCII characters hex-escaped.
	
	(We implement our own escaping mechanism here to not depend on Python's str or bytes repr.)
	"""
	
	out = []
	# The bytestring is decoded as Latin-1 instead of ASCII here so that non-ASCII characters don't cause an error.
	# The conditions inside the loop ensure that only ASCII characters are actually output.
	for byte, char in zip(bs, bs.decode("latin-1")):
		if char in {quote, "\\"}:
			out.append(f"\\{char}")
		elif char.isprintable() and byte < 0x80:
			out.append(char)
		else:
			out.append(f"\\x{byte:02x}")
	
	return "".join(out)


def bytes_quote(bs: bytes, quote: str) -> str:
	"""Convert a bytestring to a quoted ASCII string,
	with non-printable characters hex-escaped.
	
	(We implement our own escaping mechanism here to not depend on Python's str or bytes repr.)
	"""
	
	return quote + bytes_escape(bs, quote=quote) + quote


def make_subcommand_parser(subs: typing.Any, name: str, *, help: str, description: str, **kwargs: typing.Any) -> argparse.ArgumentParser:
	"""Add a subcommand parser with some slightly modified defaults to a subcommand set.
	
	This function is used to ensure that all subcommands use the same base configuration for their ArgumentParser.
	"""
	
	ap = subs.add_parser(
		name,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		help=help,
		description=description,
		allow_abbrev=False,
		add_help=False,
		**kwargs,
	)
	
	ap.add_argument("--help", action="help", help="Display this help message and exit.")
	
	return ap


def read_icns(file: str) -> api.IconFamily:
	if file == "-":
		return api.IconFamily.from_stream(sys.stdin.buffer)
	else:
		return api.IconFamily.from_file(file)


ICON_FAMILY_DESCRIPTIONS: typing.Dict[bytes, str] = {
	b"icns": "icon family",
	b"tile": '"tile" variant',
	b"over": '"rollover" variant',
	b"drop": '"drop" variant',
	b"open": '"open" variant',
	b"odrp": '"open drop" variant',
	b"sbpp": "sidebar unselected (?) variant",
	b"sbtp": 'sidebar icon ("template") variant',
	b"slct": "selected variant",
	b"\xfd\xd9/\xa8": "dark mode variant",
}

ICON_TYPE_DESCRIPTIONS: typing.Dict[typing.Type[api.ParsedElement], str] = {
	api.UnknownParsedElement: "unknown type",
	api.InvalidParsedElement: "invalid data",
	api.TableOfContents: "table of contents",
	api.IconComposerVersion: "Icon Composer version",
	api.InfoDictionary: "info dictionary",
	api.Icon1BitAndMask: "1-bit monochrome icon and 1-bit mask",
	api.Icon4Bit: "4-bit indexed color icon",
	api.Icon8Bit: "8-bit indexed color icon",
	api.IconRGB: "24-bit RGB icon",
	api.Icon8BitMask: "8-bit mask",
	api.IconARGB: "32-bit ARGB icon",
	api.IconPNG: "PNG icon",
	api.IconJPEG2000: "JPEG 2000 icon",
}

ICON_FAMILY_EXTRACT_NAMES: typing.Dict[bytes, str] = {
	b"icns": "icon family",
	b"tile": "tile variant",
	b"over": "rollover variant",
	b"drop": "drop variant",
	b"open": "open variant",
	b"odrp": "open drop variant",
	b"sbpp": "sidebar unselected variant",
	b"sbtp": "sidebar icon variant",
	b"slct": "selected variant",
	b"\xfd\xd9/\xa8": "dark mode variant",
}

ICON_TYPE_EXTRACT_NAMES: typing.Dict[typing.Type[api.IconBase], str] = {
	api.Icon1BitAndMask: "1-bit with 1-bit mask",
	api.Icon4Bit: "4-bit",
	api.Icon8Bit: "8-bit",
	api.IconRGB: "RGB",
	api.Icon8BitMask: "8-bit mask",
	api.IconARGB: "ARGB",
}


def list_icon_family(family_type: bytes, family: api.IconFamily) -> typing.Iterator[str]:
	family_desc = ICON_FAMILY_DESCRIPTIONS[family_type]
	yield f"{family_desc}, {len(family.elements)} elements:"
	
	for element in family.elements.values():
		quoted_element_type = bytes_quote(element.type, "'")
		parsed_data = element.parsed
		if isinstance(parsed_data, api.IconFamily):
			it = iter(list_icon_family(element.type, parsed_data))
			yield f"\t{quoted_element_type} ({len(element.data)} bytes): {next(it)}"
			for line in it:
				yield "\t" + line
		else:
			type_desc = ICON_TYPE_DESCRIPTIONS[type(parsed_data)]
			
			if isinstance(parsed_data, (api.UnknownParsedElement, api.InvalidParsedElement)):
				size_desc = f"{len(parsed_data.data)} bytes"
			elif isinstance(parsed_data, api.TableOfContents):
				size_desc = f"{len(parsed_data.entries)} entries"
			elif isinstance(parsed_data, api.IconComposerVersion):
				size_desc = f"value {parsed_data.version}"
			elif isinstance(parsed_data, api.InfoDictionary):
				size_desc = f"{len(parsed_data.archived_data)} bytes"
			elif isinstance(parsed_data, api.IconBase):
				size_desc = str(parsed_data.resolution)
			else:
				raise AssertionError(f"Unhandled element type: {type(parsed_data)}")
			
			yield f"\t{quoted_element_type} ({len(element.data)} bytes): {type_desc}, {size_desc}"


def do_list(ns: argparse.Namespace) -> typing.NoReturn:
	for line in list_icon_family(b"icns", read_icns(ns.file)):
		print(line)
	
	sys.exit(0)


def extract_icon_family(family: api.IconFamily, output_dir: pathlib.Path) -> typing.Iterable[str]:
	output_dir.mkdir()
	yield f"Extracting into {output_dir!r}."
	for element in family.elements.values():
		parsed_data = element.parsed
		if isinstance(parsed_data, (api.UnknownParsedElement, api.InvalidParsedElement)):
			# Dump unknown or invalid data unmodified into a .dat file with a unique name.
			desc = "unknown" if isinstance(parsed_data, api.UnknownParsedElement) else "invalid"
			name = f"0x{element.type.hex()} ({desc}).dat"
			data = element.data
		elif isinstance(parsed_data, api.IconFamily):
			# Convert nested icon family to a standalone file by adding an ICNS header.
			name = ICON_FAMILY_EXTRACT_NAMES[element.type] + ".icns"
			icns_header = b"icns" + (len(element.data) + 8).to_bytes(4, "big")
			data = icns_header + element.data
		elif isinstance(parsed_data, api.TableOfContents):
			# Convert TOC to a JSON format
			# (probably not very useful on its own).
			name = "table of contents.json"
			json_entries: typing.List[typing.Dict[str, typing.Any]] = []
			for entry in parsed_data.entries:
				json_entries.append({
					"type": entry.type.decode("latin1"),
					"element_length": entry.element_length,
				})
			data = json.dumps(json_entries, indent="\t").encode()
		elif isinstance(parsed_data, api.IconComposerVersion):
			# Convert Icon Composer version to JSON
			# (wrapped in an object because JSON only allows arrays or objects at top level).
			name = "Icon Composer version.json"
			data = json.dumps({"version": parsed_data.version}, indent="\t").encode()
		elif isinstance(parsed_data, api.InfoDictionary):
			# Info dictionary is in (binary) plist format and can be written straight to a .plist file.
			name = "info dictionary.plist"
			data = parsed_data.archived_data
		elif isinstance(parsed_data, api.IconBase):
			size_desc = str(parsed_data.resolution)
			
			if isinstance(parsed_data, api.IconPNG):
				# Icons in PNG format can be written straight to a file.
				name = f"{size_desc}.png"
				data = element.data
			elif isinstance(parsed_data, api.IconJPEG2000):
				# Icons in JPEG 2000 format can be written straight to a file.
				name = f"{size_desc}.jp2"
				data = element.data
			else:
				# Other icons are stored as raw bitmaps that can't be stored directly as standalone files.
				# These icons are converted to PNG via Pillow.
				type_desc = ICON_TYPE_EXTRACT_NAMES[type(parsed_data)]
				assert element.known_type is not None
				if element.known_type.data_type == element_types.DataType.icon_png_jp2_rgb:
					# Add an explanatory suffix to differentiate RGB bitmaps in PNG/JPEG 2000 elements from the normal RGB bitmap elements.
					# This is done in part because this variation is rare enough that it's worth pointing it out,
					# and in part to prevent file name conflicts in the very unlikely case that an icon family contains both a PNG/JPEG 2000 element with RGB bitmap data and a regular RGB bitmap element
					# ('icp4' and 'is32', or 'icp5' and 'il32').
					type_desc += " (in PNG-JPEG 2000 element)"
				name = f"{size_desc} {type_desc}.png"
				with io.BytesIO() as f:
					if isinstance(parsed_data, (api.IconWithMask, api.Mask)):
						image = parsed_data.to_pil_image()
					elif isinstance(parsed_data, api.IconWithoutMask):
						try:
							mask_image = family.mask_image_for_resolution(parsed_data.resolution)
						except ValueError:
							mask_image = None
						image = parsed_data.to_pil_image(mask_image)
					else:
						raise AssertionError(f"Unhandled icon type: {type(parsed_data)}")
					image.save(f, "PNG")
					data = f.getvalue()
		else:
			raise AssertionError(f"Unhandled element type: {type(parsed_data)}")
		
		quoted_element_type = bytes_quote(element.type, "'")
		yield f"Extracting {quoted_element_type} ({len(element.data)} bytes) to {name!r} ({len(data)} bytes)..."
		with (output_dir / name).open("xb") as outf:
			outf.write(data)
		
		if isinstance(parsed_data, api.IconFamily):
			# Recursively extract nested icon families
			# (in addition to writing them to .icns files above).
			for line in extract_icon_family(parsed_data, output_dir / (name + ".extracted")):
				yield "\t" + line


def do_extract(ns: argparse.Namespace) -> typing.NoReturn:
	if ns.output_dir is None:
		ns.output_dir = ns.file + ".extracted"
	
	for line in extract_icon_family(read_icns(ns.file), pathlib.Path(ns.output_dir)):
		print(line)
	
	sys.exit(0)


def main() -> typing.NoReturn:
	"""Main function of the CLI.
	
	This function is a valid setuptools entry point.
	Arguments are passed in sys.argv,
	and every execution path ends with a sys.exit call.
	(setuptools entry points are also permitted to return an integer,
	which will be treated as an exit code.
	We do not use this feature and instead always call sys.exit ourselves.)
	"""
	
	ap = argparse.ArgumentParser(
		description="""
%(prog)s is a tool for inspecting Apple icon images (ICNS images),
as stored in .icns files and 'icns' resources.
""",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		allow_abbrev=False,
		add_help=False,
	)
	
	ap.add_argument("--help", action="help", help="Display this help message and exit.")
	ap.add_argument("--version", action="version", version=__version__, help="Display version information and exit.")
	
	subs = ap.add_subparsers(
		dest="subcommand",
		# TODO Add required=True (added in Python 3.7) once we drop Python 3.6 compatibility.
		metavar="SUBCOMMAND",
	)
	
	ap_list = make_subcommand_parser(
		subs,
		"list",
		help="List the icons (and other data) stored in an ICNS image.",
		description="""
List the icons (and other data) stored in an ICNS image.
""",
	)
	
	ap_list.add_argument("file", help="The file from which to read the ICNS image, or - for stdin.")
	
	ap_extract = make_subcommand_parser(
		subs,
		"extract",
		help="Extract the icons (and other data) from an ICNS image into a directory.",
		description="""
Extract the icons (and other data) from an ICNS image into a directory.
""",
	)
	
	ap_extract.add_argument("-o", "--output-dir", default=None, help="The directory into which to extract the files. This directory must not exist yet. Default: input file name with the suffix .extracted appended.")
	
	ap_extract.add_argument("file", help="The file from which to read the ICNS image, or - for stdin.")
	
	ns = ap.parse_args()
	
	if ns.subcommand is None:
		# TODO Remove this branch once we drop Python 3.6 compatibility, because this case will be handled by passing required=True to add_subparsers (see above).
		print("Missing subcommand", file=sys.stderr)
		sys.exit(2)
	elif ns.subcommand == "list":
		do_list(ns)
	elif ns.subcommand == "extract":
		do_extract(ns)
	else:
		raise AssertionError(f"Subcommand not handled: {ns.subcommand!r}")


if __name__ == "__main__":
	sys.exit(main())
