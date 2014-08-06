#!/usr/bin/env python
import os, re, sys, subprocess;
try:
	raise ImportError(); # Don't pywin32 because it does not properly create directory shortcuts (???)
	import win32com.client;
except ImportError:
	win32com = None;
version_info = [ 1 , 0 ];



# Python 2/3 support
if (sys.version_info[0] == 3):
	# Version 3
	def py_2or3_str_to_bytes(text, encoding="ascii", errors="strict"):
		return bytes(text, encoding, errors);
	def py_2or3_bytes_to_str(text, encoding="ascii", errors="strict"):
		return text.decode(encoding, errors);
	def py_2or3_byte_ord(char):
		return char;
else:
	# Version 2
	def py_2or3_str_to_bytes(text, encoding="ascii", errors="strict"):
		return text.encode(encoding, errors);
	def py_2or3_bytes_to_str(text, encoding="ascii", errors="strict"):
		return text.decode(encoding, errors);
	def py_2or3_byte_ord(char):
		return ord(char);



# Get a unique file name
def open_mode_string_to_os_flags(open_mode):
	binary = False;
	flags = 0;

	# Binary
	if (len(open_mode) > 0 and open_mode[-1] == "b"):
		binary = True;
		open_mode = open_mode[0 : -1];
		try: flags |= os.O_BINARY;
		except AttributeError: pass;

	# Mode detection
	if (open_mode == "a"):
		flags |= os.O_APPEND;
	elif (open_mode == "r"):
		flags |= os.O_RDONLY;
	elif (open_mode == "r+"):
		flags |= os.O_RDWR;
	elif (open_mode == "w"):
		flags |= os.O_WRONLY;
	else:
		raise ValueError("Invalid mode ({0:s})".format(open_mode));

	# Done
	return flags;

def get_unique_filename(filename, suffix=None, id_start=0, id_prefix="[" , id_suffix="]", id_limit=-1, open_mode=None, return_none=False):
	# Setup
	filename = os.path.abspath(filename);
	if (suffix is None):
		prefix, suffix = os.path.splitext(filename);
	else:
		prefix = filename;

	# Begin
	fn = prefix + suffix;
	fd = None;
	has_limit = (id_limit > id_start);
	os_open_flags = os.O_CREAT | os.O_EXCL;
	if (open_mode is not None):
		os_open_flags |= open_mode_string_to_os_flags(open_mode);

	while (True):
		if (open_mode is not None):
			# Open as a descriptor
			try:
				fd = os.open(fn, os_open_flags);
				fd = os.fdopen(fd, open_mode);
				break;
			except OSError:
				# Not unique
				fd = None;
		else:
			# Filename is unique
			if (not os.path.exists(fn)): break;

		# Update filename
		fn = "{0:s}{1:s}{2:d}{3:s}{4:s}".format(prefix, id_prefix, id_start, id_suffix, suffix);

		# Update id
		id_start += 1;

		# Limit
		if (has_limit and id_start >= id_limit):
			if (return_none): return None;
			break;

	# Done
	if (open_mode is not None):
		# Filename and descriptor
		return ( fn , fd );
	else:
		# Filename
		return fn;



# Convert a list of arguments into a string of arguments which can be executed on the command line
def argument_list_to_command_line_string(arguments, forced):
	args_new = [];
	re_valid_pattern = re.compile(r"^[a-zA-Z0-9_\-\.\+\\/]+$");
	for arg in arguments:
		# Format the argument
		if (forced or re_valid_pattern.match(arg) is None):
			arg = '"{0:s}"'.format(arg.replace('"', '""'));

		# Add
		args_new.append(arg);

	# Join and return
	return " ".join(args_new);



# Argument parser
def arguments_parse(arguments, start, descriptor, flagless_argument_order=[], stop_after_all_flagless=False, return_level=0):
	# Setup data
	argument_values = {};
	argument_aliases_short = {};
	argument_aliases_long = {};
	errors = [];

	for k,v in descriptor.items():
		if ("bool" in v and v["bool"] == True):
			argument_values[k] = False;
		else:
			argument_values[k] = None;

		if ("short" in v):
			for flag in v["short"]:
				argument_aliases_short[flag] = k;

		if ("long" in v):
			for flag in v["long"]:
				argument_aliases_long[flag] = k;

	# Parse command line
	end = len(arguments);
	while (start < end):
		# Check
		arg = arguments[start];
		if (len(arg) > 0 and arg[0] == "-"):
			if (len(arg) == 1):
				# Single "-"
				errors.append("Invalid argument {0:s}".format(repr(arg)));
			else:
				if (arg[1] == "-"):
					# Long argument
					arg = arg[2 : ];
					if (arg in argument_aliases_long):
						# Set
						arg_key = argument_aliases_long[arg];
						if (argument_values[arg_key] == False or argument_values[arg_key] == True):
							# No value
							argument_values[arg_key] = True;
						else:
							if (start + 1 < end):
								# Value
								start += 1;
								argument_values[arg_key] = arguments[start];
							else:
								# Invalid
								errors.append("No value specified for flag {0:s}".format(repr(arg)));

						# Remove from flagless_argument_order
						if (arg_key in flagless_argument_order):
							flagless_argument_order.pop(flagless_argument_order.index(arg_key));
					else:
						# Invalid
						errors.append("Invalid long flag {0:s}".format(repr(arg)));

				else:
					# Short argument(s)
					arg = arg[1 : ];
					arg_len = len(arg);
					i = 0;
					while (i < arg_len):
						if (arg[i] in argument_aliases_short):
							# Set
							arg_key = argument_aliases_short[arg[i]];
							if (argument_values[arg_key] == False or argument_values[arg_key] == True):
								# No value
								argument_values[arg_key] = True;
							else:
								if (i + 1 < arg_len):
									# Trailing value
									argument_values[arg_key] = arg[i + 1 : ];
									i = arg_len; # Terminate
								elif (start + 1 < end):
									# Value
									start += 1;
									argument_values[arg_key] = arguments[start];
								else:
									# Invalid
									errors.append("No value specified for flag {0:s}".format(repr(arg)));

							# Remove from flagless_argument_order
							if (arg_key in flagless_argument_order):
								flagless_argument_order.pop(flagless_argument_order.index(arg_key));
						else:
							# Invalid
							in_str = "";
							if (arg[i] != arg): in_str = " in {0:s}".format(repr(arg));
							errors.append("Invalid short flag {0:s}{1:s}".format(repr(arg[i]), in_str));

						# Next
						i += 1;

		elif (len(flagless_argument_order) > 0):
			# Set
			arg_key = flagless_argument_order[0];
			if (argument_values[arg_key] == False or argument_values[arg_key] == True):
				# No value
				argument_values[arg_key] = True;
			else:
				# Value
				argument_values[arg_key] = arg;

			# Remove from flagless_argument_order
			flagless_argument_order.pop(0);
		else:
			# Invalid
			errors.append("Invalid argument {0:s}".format(repr(arg)));

		# Next
		start += 1;
		if (stop_after_all_flagless and len(flagless_argument_order) == 0): break; # The rest are ignored

	# Return
	if (return_level <= 0):
		return argument_values;
	else:
		return ( argument_values , errors , flagless_argument_order , start )[0 : return_level + 1];



# Create a shortcut to a webpage or similar
def create_internet_shortcut(filename, target, icon=None, wdir=None):
	shortcut = file(filename, "wb");
	shortcut.write("[InternetShortcut]\r\nURL={0:s}".format(target));
	if (icon):
		if (isinstance(icon, tuple) or isinstance(icon, list)):
			if (len(icon) >= 2):
				icon_file = icon[0];
				icon_index = icon[1];
			else:
				icon_file = icon[0];
				icon_index = 0;
		else:
			icon_file = icon;
			icon_index = 0;
		shortcut.write("\r\nIconFile={0:s}".format(icon_file));
		shortcut.write("\r\nIconIndex={0:d}".format(icon_index));
	if (wdir):
		shortcut.write("\r\nWorkingDirectory={0:s}".format(wdir));
	shortcut.close();

	return None;



# Create a shortcut to an executable file
def create_shortcut(filename, target, icon=None, wdir=None):
	# Argument setup
	if (isinstance(target, tuple) or isinstance(target, list)):
		target_file = target[0];
		arguments = target[1 : ];
	else:
		target_file = target;
		arguments = [];

	if (icon):
		if (isinstance(icon, tuple) or isinstance(icon, list)):
			if (len(icon) >= 2):
				icon_file = "{0:s}, {1:d}".format(icon[0], icon[1]);
			else:
				icon_file = icon[0];
		else:
			icon_file = icon;
	else:
		icon_file = None;


	# cscript subprocess or pywin32 version?
	if (win32com is None):
		def vbscript_escape(text):
			return text.replace('"', '""');

		# Setup cscript source
		script = [
			'Set shell = WScript.CreateObject("WScript.Shell")',
			'Set shortcut = shell.CreateShortcut("{0:s}")'.format(vbscript_escape(filename)),
			'shortcut.TargetPath = "{0:s}"'.format(vbscript_escape(target_file)),
			'shortcut.Arguments = "{0:s}"'.format(vbscript_escape(argument_list_to_command_line_string(arguments, False))),
		];

		if (icon_file is not None):
			script.append('shortcut.IconLocation = Unescape("{0:s}")'.format(icon_file));
		if (wdir):
			script.append('shortcut.WorkingDirectory = Unescape("{0:s}")'.format(wdir));

		script.append('shortcut.Save');

		# Write
		fn, fd = get_unique_filename(os.path.abspath(sys.argv[0]) + ".vbscript", ".txt", open_mode="wb");
		fd.write(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(script)), "utf-8"));
		fd.close();

		# Execute command
		cmd = [ "CScript.exe" , "//E:vbscript" , "//Nologo" , "//B" , fn ];
		error = None;
		try:
			p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
		except OSError:
			error = "CScript.exe could not be executed";
		if (error is None): p.communicate();

		# Delete
		try:
			os.remove(fn);
		except OSError:
			pass;

		# Error
		if (error is not None):
			return error;
		elif (p.returncode != 0):
			return "CScript.exe returned {0:s}".format(str(p.returncode));

		# Okay
		return None;

	else:
		# pywin32
		shell = win32com.client.Dispatch("wscript.shell");
		shortcut = shell.CreateShortcut(filename);

		try:
			shortcut.TargetPath = argument_list_to_command_line_string([ target_file ], True);
		except AttributeError:
			return "Invalid target";
		try:
			shortcut.Arguments = argument_list_to_command_line_string(arguments, False);
		except AttributeError:
			return "Invalid arguments";

		if (icon_file is not None):
			try:
				shortcut.IconLocation = icon_file;
			except AttributeError:
				return "Invalid icon";
		if (wdir):
			try:
				shortcut.WorkingDirectory = wdir;
			except AttributeError:
				return "Invalid working directory";

		shortcut.Save();

		# Okay
		return None;



# Usage info
def usage(arguments_descriptor, stream):
	usage_info = [
		"Usage:",
		"    {0:s} [options] shortcut_filename shortcut_target [shortcut_arguments...]".format(os.path.split(sys.argv[0])[1]),
		"\n",
		"Available flags:",
	];

	# Flags
	argument_keys = sorted(arguments_descriptor.keys());

	for i in range(len(argument_keys)):
		key = argument_keys[i];
		arg = arguments_descriptor[key];
		param_name = "";
		if (not ("bool" in arg and arg["bool"])):
			if ("argument" in arg):
				param_name = " <{0:s}>".format(arg["argument"]);
			else:
				param_name = " <value>";

		if (i > 0):
			usage_info.append("");

		if ("long" in arg):
			for a in arg["long"]:
				usage_info.append("  --{0:s}{1:s}".format(a, param_name));

		if ("short" in arg):
			usage_info.append("  {0:s}".format(", ".join([ "-{0:s}{1:s}".format(a, param_name) for a in arg["short"] ])));

		if ("description" in arg):
			usage_info.append("    {0:s}".format(arg["description"]));

	# Extra
	usage_info.extend([
		"\n",
		"Notes:",
		"    Once shortcut_filename and shortcut_target have been specified,",
		"    all remaining arguments are treated as shortcut execution arguments.",
		"",
		"    The extension .lnk is used for operating system shortcuts, and .url",
		"    for web (and other) shortcuts. If no extension is specified in the filename,",
		"    one is automatically added.",
	]);

	# Output
	stream.write("{0:s}\n".format("\n".join(usage_info)));



# Main
def main():
	# Command line argument settings
	arguments_descriptor = {
		"version": {
			"short": [ "v" ],
			"long": [ "version" ],
			"bool": True,
			"description": "Show version info and exit",
		},
		"help": {
			"short": [ "h" , "?" ],
			"long": [ "help" , "usage" ],
			"bool": True,
			"description": "Show usage info and exit",
		},
		"icon": {
			"short": [ "i" ],
			"long": [ "icon" ],
			"argument": "path",
			"description": "The icon file path to be used for the shortcut",
		},
		"icon-index": {
			"short": [ "I" ],
			"long": [ "icon-index" ],
			"argument": "number",
			"description": "The index of the icon in the icon file to be used; defaults to 0",
		},
		"wdir": {
			"short": [ "d" ],
			"long": [ "working-directory" , "directory" ],
			"argument": "path",
			"description": "The working directory to be used for the shortcut",
		},
		"filename": {
			"short": [ "o" ],
			"long": [ "filename" , "output" ],
			"argument": "path",
			"description": "The filename of the shortcut (same as shortcut_filename)",
		},
		"target": {
			"short": [ "t" ],
			"long": [ "target" ],
			"argument": "path",
			"description": "The target to be executed when the shortcut is used (same as shortcut_target)",
		},
	};
	arguments, errors, flagless, start = arguments_parse(sys.argv, 1, arguments_descriptor, flagless_argument_order=[ "filename" , "target" ], stop_after_all_flagless=True, return_level=3);



	# Command line parsing errors?
	if (len(errors) > 0):
		for e in errors:
			sys.stderr.write("{0:s}\n".format(e));
		return -1;



	# Version
	if (arguments["version"]):
		sys.stdout.write("Version {0:s}\n".format(".".join([ str(v) for v in version_info ])));
		return 0;

	if (arguments["help"]):
		# Usage info
		usage(arguments_descriptor, sys.stdout);
		return 0;



	# Complete?
	if (
		arguments["filename"] is None or
		arguments["target"] is None
	):
		usage(arguments_descriptor, sys.stderr);
		return -1;



	# Format arguments
	if (arguments["icon"] is None):
		# No icon
		icon = None;
	else:
		# Format icon
		icon_file = os.path.abspath(arguments["icon"]);
		if (arguments["icon-index"] is None):
			icon_index = 0;
		else:
			try:
				icon_index = int(arguments["icon-index"], 10);
			except ValueError:
				icon_index = 0;
		icon = ( icon_file , icon_index );

	if (arguments["wdir"] is None):
		# No working directory
		wdir = None;
	else:
		# Format properly
		wdir = os.path.abspath(arguments["wdir"]);

	filename = os.path.abspath(arguments["filename"]);



	# Check the protocol
	re_protocol = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9\-\+\.]*):");
	match = re_protocol.match(arguments["target"]);
	if (match is not None and len(match.group(1)) > 1):
		# Internet
		if (os.path.splitext(filename)[1].lower() != ".url"): filename += ".url";
		error = create_internet_shortcut(filename, arguments["target"], icon=icon, wdir=wdir);
	else:
		# OS
		if (os.path.splitext(filename)[1].lower() != ".lnk"): filename += ".lnk";
		target_file = os.path.abspath(arguments["target"]);
		target = [ target_file , ] + sys.argv[start : ];
		error = create_shortcut(filename, target, icon=icon, wdir=wdir);



	# Error
	if (error is not None):
		sys.stderr.write("{0:s}\n".format(error));
		return 1;



	# Done
	return 0;



# Execute
if (__name__ == "__main__"): sys.exit(main());

