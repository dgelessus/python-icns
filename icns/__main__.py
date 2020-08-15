import argparse
import sys
import typing

from . import __version__, api


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


ICON_TYPE_DESCRIPTIONS: typing.Dict[typing.Type[api.ParsedElement], str] = {
	api.TableOfContents: "table of contents",
	api.IconComposerVersion: "Icon Composer version",
	api.InfoDictionary: "info dictionary",
	api.Icon1BitAndMask: "1-bit monochrome icon and 1-bit mask",
	api.Icon4Bit: "4-bit indexed color icon",
	api.Icon8Bit: "8-bit indexed color icon",
	api.IconRGB: "24-bit RGB icon",
	api.Icon8BitMask: "8-bit mask",
	api.IconARGB: "32-bit ARGB icon",
	api.IconPNGOrJPEG2000: "PNG or JPEG 2000 icon",
}


def list_icon_family(family: api.IconFamily) -> typing.Iterator[str]:
	yield f"icon family, {len(family.elements)} elements:"
	
	for element in family.elements.values():
		quoted_element_type = bytes_quote(element.type, "'")
		parsed_data = element.parsed
		if isinstance(parsed_data, api.IconFamily):
			it = iter(list_icon_family(parsed_data))
			yield f"\t{quoted_element_type} ({len(element.data)} bytes): {next(it)}"
			for line in it:
				yield "\t" + line
		else:
			if isinstance(parsed_data, api.IconPNGOrJPEG2000):
				if parsed_data.is_png:
					type_desc = "PNG icon"
				elif parsed_data.is_jpeg_2000:
					type_desc = "JPEG 2000 icon"
				else:
					type_desc = "invalid PNG or JPEG 2000 icon"
			else:
				type_desc = ICON_TYPE_DESCRIPTIONS[type(parsed_data)]
			
			if isinstance(parsed_data, api.TableOfContents):
				size_desc = f"{len(parsed_data.entries)} entries"
			elif isinstance(parsed_data, api.IconComposerVersion):
				size_desc = f"value {parsed_data.version}"
			elif isinstance(parsed_data, api.InfoDictionary):
				size_desc = f"{len(parsed_data.archived_data)} bytes"
			elif isinstance(parsed_data, api.Icon):
				size_desc = f"{parsed_data.pixel_width}x{parsed_data.pixel_height}"
				if parsed_data.scale != 1:
					size_desc += f" ({parsed_data.point_width}x{parsed_data.point_height}@{parsed_data.scale}x)"
			else:
				raise AssertionError(f"Unhandled element type: {type(element)}")
			
			yield f"\t{quoted_element_type} ({len(element.data)} bytes): {type_desc}, {size_desc}"


def do_list(ns: argparse.Namespace) -> typing.NoReturn:
	if ns.file == "-":
		main_family = api.IconFamily.from_stream(sys.stdin.buffer)
	else:
		main_family = api.IconFamily.from_file(ns.file)
	
	for line in list_icon_family(main_family):
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
		required=True,
		metavar="SUBCOMMAND",
	)
	
	ap_list = make_subcommand_parser(
		subs,
		"list",
		help="List the icons (and other data) stored in an ICNS image.",
		description=f"""
List the icons (and other data) stored in an ICNS image.
""",
	)
	
	ap_list.add_argument("file", help="The file from which to read the ICNS image, or - for stdin.")
	
	ns = ap.parse_args()
	
	if ns.subcommand == "list":
		do_list(ns)
	else:
		raise AssertionError(f"Subcommand not handled: {ns.subcommand!r}")


if __name__ == "__main__":
	sys.exit(main())
