#!/usr/bin/env python
import os, re, sys, time, subprocess;
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



# Helper functions
class DiskPart:
	re_generic_id = re.compile(r"([0-9]+)", re.I);


	class Table:
		def __init__(self, table_str=None):
			self.format = None;
			self.rows = None;
			self.row_infos = None;
			self.info = None;

			if (table_str is not None): self.parse(table_str);

		def parse(self, table_str):
			re_separation_line = re.compile(r"^\s*(-+\s+)*-+\s*$");
			re_separation = re.compile(r"-+");
			re_info_format = re.compile(r"^\s*(.*?)\s*:\s*(.*)\s*$", re.DOTALL);

			# Find separator line
			lines = table_str.splitlines();
			table_sep_line = -1;
			for i in range(len(lines)):
				if (re_separation_line.search(lines[i]) is not None and i > 0):
					table_sep_line = i;
					break;

			# No table?
			if (table_sep_line < 0): return False;

			# Label regions
			regions = [];
			for match in re_separation.finditer(lines[table_sep_line]):
				regions.append(match.start(0));

			# Labels
			self.format = [];
			for i in range(len(regions) - 1):
				self.format.append(lines[table_sep_line - 1][regions[i] : regions[i + 1]].strip());
			i = len(regions) - 1;
			self.format.append(lines[table_sep_line - 1][regions[i] : ].strip());

			# Setup data
			self.rows = [];
			self.row_infos = [];
			last_line = len(lines);
			for i in range(table_sep_line + 1, len(lines)):
				# Empty line
				if (len(lines[i].strip()) == 0):
					last_line = i + 1;
					break;

				# Parse
				data = {};
				for j in range(len(self.format) - 1):
					data[self.format[j]] = lines[i][regions[j] : regions[j + 1]].strip();
				j = len(self.format) - 1;
				data[self.format[j]] = lines[i][regions[j] : ].strip();
				self.rows.append(data);
				self.row_infos.append(None);


			# Setup info
			self.info = {};
			for i in range(last_line, len(lines)):
				match = re_info_format.search(lines[i]);
				if (match is not None):
					self.info[match.group(1)] = match.group(2);

			# Done
			return True;



	@classmethod
	def stdout_to_sections(cls, stdout):
		re_section = re.compile(r"diskpart>([^\n]*\n)(.*?)(diskpart>|$)", re.I | re.DOTALL);
		re_strip_empty_lines = re.compile(r"^(\s*?\n)+|(\n\s*?)+$");
		search_string = stdout;
		sections = [];
		while (True):
			match = re_section.search(search_string);
			if (match is None): break;

			# Add
			sections.append(re_strip_empty_lines.sub("", match.group(2)));

			# Next
			search_string = search_string[match.start(3) : ];

		return sections;

	@classmethod
	def is_same_file(cls, path1, path2):
		return (os.path.abspath(path1).lower() == os.path.abspath(path2).lower());

	@classmethod
	def is_same_drive_label(cls, label1, label2):
		return (label1.lower() == label2.lower());

	@classmethod
	def get_tables(cls, additional_inputs=None):
		# Get info
		inputs = [];
		offset = 0;
		if (additional_inputs is not None):
			offset = len(additional_inputs);
			inputs.extend(additional_inputs);
		inputs.extend([
			"LIST DISK",
			"LIST VDISK",
			"LIST VOLUME",
		]);
		cmd = [ "DiskPart.exe" ];

		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
		pr = p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));


		# Sections
		sections = DiskPart.stdout_to_sections(py_2or3_bytes_to_str(pr[0], "utf-8"));



		# Enumerate disks
		disk_table = DiskPart.Table(sections[offset + 0]);
		vdisk_table = DiskPart.Table(sections[offset + 1]);
		volume_table = DiskPart.Table(sections[offset + 2]);



		# Get volume information
		inputs = [];
		info_list = [];

		# Disks
		table = disk_table;
		if (table.rows is not None):
			for i in range(len(table.rows)):
				match = DiskPart.re_generic_id.search(table.rows[i]["Disk ###"]);
				if (match is None):
					input_id = -1;
				else:
					data_id = int(match.group(1), 10);
					inputs.append("SELECT DISK {0:d}".format(data_id));
					inputs.append("DETAIL DISK");
					input_id = len(inputs) - 1;

				info_list.append({
					"table": table,
					"row_id": i,
					"input_id": input_id,
				});

		# Volumes
		table = volume_table;
		if (table.rows is not None):
			for i in range(len(table.rows)):
				match = DiskPart.re_generic_id.search(table.rows[i]["Volume ###"]);
				if (match is None):
					input_id = -1;
				else:
					data_id = int(match.group(1), 10);
					inputs.append("SELECT VOLUME {0:d}".format(data_id));
					inputs.append("DETAIL VOLUME");
					input_id = len(inputs) - 1;

				info_list.append({
					"table": table,
					"row_id": i,
					"input_id": input_id,
				});

		# Vdisks
		table = vdisk_table;
		if (table.rows is not None):
			for i in range(len(table.rows)):
				info_list.append({
					"table": table,
					"row_id": i,
					"input_id": -1,
				});

		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
		pr = p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));


		# Parse info
		sections = DiskPart.stdout_to_sections(py_2or3_bytes_to_str(pr[0], "utf-8"));
		for info in info_list:
			# Parse a new table
			if (info["input_id"] >= 0):
				table = DiskPart.Table(sections[info["input_id"]]);
			else:
				table = None;

			# Apply
			info["table"].row_infos[info["row_id"]] = table;



		# Return tables
		return {
			"disk": disk_table,
			"volume": volume_table,
			"vdisk": vdisk_table,
		};



# Commands
def command_unmount(path, drive_letter):
	# Argument formatting
	path = os.path.abspath(path);


	# Info
	tables = DiskPart.get_tables();
	disk_table = tables["disk"];
	vdisk_table = tables["vdisk"];
	volume_table = tables["volume"];

	# Search for the proper disk
	target_vdisk = None;
	if (vdisk_table.rows is None):
		return "Virtual disk does not exist";

	for row in vdisk_table.rows:
		if (DiskPart.is_same_file(path, row["File"])):
			target_vdisk = row;
			break;

	# Find relevant volume
	remove_drive_letter_input = [];
	if (target_vdisk is not None):
		match = DiskPart.re_generic_id.search(target_vdisk["Disk ###"]);
		if (match is None):
			target_disk_id = -1;
		else:
			target_disk_id = int(match.group(1), 10);

		target_volume_table_ids = [];
		for i in range(len(volume_table.rows)):
			if (volume_table.row_infos[i] is None): continue; # No info table
			if (len(volume_table.row_infos[i].rows) > 0):
				match = DiskPart.re_generic_id.search(volume_table.row_infos[i].rows[0]["Disk ###"]);
				if (match is not None):
					disk_id = int(match.group(1), 10);
					if (target_disk_id == disk_id):
						target_volume_table_ids.append(i);

		# Target volume
		if (len(target_volume_table_ids) == 1):
			target_volume_table_id = target_volume_table_ids[0];
			current_drive_letter = volume_table.rows[target_volume_table_id]["Ltr"];
			match = DiskPart.re_generic_id.search(volume_table.rows[target_volume_table_id]["Volume ###"]);
			if (match is not None):
				target_volume_id = int(match.group(1), 10);

				if (drive_letter is not None and len(current_drive_letter) > 0 and drive_letter != current_drive_letter):
					return "Targeted drive letter does not match";

				remove_drive_letter_input.extend([
					"SELECT VOLUME {0:d}".format(target_volume_id),
					"REMOVE LETTER=\"{0:s}\"".format(current_drive_letter),
				]);



	# Command
	inputs = [];
	inputs.extend(remove_drive_letter_input);
	inputs.extend([
		"SELECT VDISK FILE=\"{0:s}\"".format(path),
		"DETACH VDISK",
	]);


	# Execute
	cmd = [ "DiskPart.exe" ];
	p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
	p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));

	if (p.returncode != 0):
		return "DiskPart returned {0:s}".format(str(p.returncode));


	# Done
	return None;

def command_delete(path):
	# Argument formatting
	path = os.path.abspath(path);

	# Delete file
	try:
		os.remove(path);
	except OSError:
		return "Target path could not deleted";

	# Done
	return None;

def command_create(path, size, label, file_system):
	# Argument formatting
	path = os.path.abspath(path);

	if (label is None):
		label = "";
	else:
		label = label.replace('"', "");

	if (file_system is not None):
		file_system = " FS=\"{0:s}\"".format(file_system);

	# Already exists
	if (os.path.exists(path)):
		return "Target path already exists";

	# Command
	inputs = [
		"CREATE VDISK FILE=\"{0:s}\" MAXIMUM=\"{1:d}\" TYPE=FIXED".format(path, size),
		"SELECT VDISK FILE=\"{0:s}\"".format(path),
		"ATTACH VDISK",
		"CREATE PARTITION PRIMARY",
		"FORMAT LABEL=\"{0:s}\" QUICK{1:s}".format(label, file_system),
		"DETACH VDISK",
	];

	# Execute
	cmd = [ "DiskPart.exe" ];
	p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
	p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));

	if (p.returncode != 0):
		return "DiskPart returned {0:s}".format(str(p.returncode));

	# Done
	return None;

def command_mount(path, drive_letter):
	# Argument formatting
	path = os.path.abspath(path);


	# Loop a few times, because for some reason, attaching may not work
	iterations = [ 0 , 1 ];
	for iteration in iterations:
		# Get info
		cmd = [ "DiskPart.exe" ];
		inputs = [
			"SELECT VDISK FILE=\"{0:s}\"".format(path),
			"ATTACH VDISK",
		];
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
		p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));

		if (iteration > 0): time.sleep(iteration); # Sleep on iterate

		tables = DiskPart.get_tables();
		disk_table = tables["disk"];
		vdisk_table = tables["vdisk"];
		volume_table = tables["volume"];



		# Search for the proper disk
		target_vdisk = None;
		if (vdisk_table.rows is None):
			return "Virtual disk does not exist";
		elif (volume_table.rows is None):
			return "Volume info table not found";

		for row in vdisk_table.rows:
			if (DiskPart.is_same_file(path, row["File"])):
				target_vdisk = row;
				break;



		# Error?
		error = None;
		error_resumable = False;
		if (target_vdisk is None):
			error = "Error locating virtual disk; it was not attached properly or does not exist";
		else:
			# Find relevant volume
			match = DiskPart.re_generic_id.search(target_vdisk["Disk ###"]);
			if (match is None):
				target_disk_id = -1;
			else:
				target_disk_id = int(match.group(1), 10);

			target_volume_table_ids = [];
			for i in range(len(volume_table.rows)):
				if (volume_table.row_infos[i] is None): continue; # No info table
				if (len(volume_table.row_infos[i].rows) > 0):
					match = DiskPart.re_generic_id.search(volume_table.row_infos[i].rows[0]["Disk ###"]);
					if (match is not None):
						disk_id = int(match.group(1), 10);
						if (target_disk_id == disk_id):
							target_volume_table_ids.append(i);



			# Error?
			if (len(target_volume_table_ids) == 0):
				error = "Error locating volume";
				error_resumable = True;
			else:
				# Find target volume if there are more than one
				target_volume_table_id = target_volume_table_ids[0];
				if (len(target_volume_table_ids) > 1):
					error = "Could not distinguish drives";
				else:
					# Find volume id
					current_drive_letter = volume_table.rows[target_volume_table_id]["Ltr"];
					match = DiskPart.re_generic_id.search(volume_table.rows[target_volume_table_id]["Volume ###"]);
					if (match is None):
						target_volume_id = -1;
					else:
						target_volume_id = int(match.group(1), 10);



					# Mount to a drive
					if (target_volume_id < 0):
						error = "Error finding drive number";
					elif (current_drive_letter == drive_letter):
						return "Virtual drive already mounted";
					elif (len(current_drive_letter) > 0):
						return "Virtual drive already mounted to drive {0:s}".format(current_drive_letter);
					else:
						inputs = [
							"SELECT VOLUME {0:d}".format(target_volume_id),
							"ASSIGN LETTER={0:s}".format(drive_letter),
						];

						p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
						p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));

						if (p.returncode != 0):
							error = "DiskPart returned {0:s}".format(str(p.returncode));


		if (error is None or not error_resumable): break;



	# Error and detach
	if (error is not None):
		inputs = [
			"SELECT VDISK FILE=\"{0:s}\"".format(path),
			"DETACH VDISK",
		];
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
		p.communicate(py_2or3_str_to_bytes("{0:s}\n".format("\n".join(inputs)), "utf-8"));

		return error;



	# Done
	return None;



# Usage info
def usage(arguments_descriptor, stream):
	usage_info = [
		"Usage:",
		"    {0:s} <arguments>".format(os.path.split(sys.argv[0])[1]),
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
		"path": {
			"short": [ "p" ],
			"long": [ "path" ],
			"argument": "path",
			"description": "The path to the virtual disk file used for any commands",
		},
		"size": {
			"short": [ "s" ],
			"long": [ "size" ],
			"argument": "megabytes",
			"description": "The size of the virtual disk, in MiB",
		},
		"letter": {
			"short": [ "l" ],
			"long": [ "letter" ],
			"argument": "drive_letter",
			"description": "The drive letter the virtual disk should be mounted on",
		},
		"label": {
			"short": [ "L" ],
			"long": [ "label" ],
			"argument": "text",
			"description": "The label of a newly created virtual disk",
		},
		"file-system": {
			"short": [ "f" ],
			"long": [ "file-system" ],
			"argument": "text",
			"description": "The file system of a newly created virtual disk",
		},
		"create": {
			"short": [ "c" ],
			"long": [ "create" ],
			"bool": True,
			"description": "A new virtual disk file should be created",
		},
		"delete": {
			"short": [ "d" ],
			"long": [ "delete" ],
			"bool": True,
			"description": "The virtual disk file should be deleted",
		},
		"mount": {
			"short": [ "m" ],
			"long": [ "mount" ],
			"bool": True,
			"description": "The virtual disk should be mounted",
		},
		"unmount": {
			"short": [ "u" ],
			"long": [ "unmount" ],
			"bool": True,
			"description": "The virtual disk should be unmounted",
		},
		"stop-on-error": {
			"long": [ "stop-on-error" ],
			"bool": True,
			"description": "If any error occurs while performing commands, the command sequence should be stopped",
		},
	};
	arguments, errors = arguments_parse(sys.argv, 1, arguments_descriptor, return_level=1);



	# Command line parsing errors?
	if (len(errors) > 0):
		for e in errors:
			sys.stderr.write("{0:s}\n".format(e));
		sys.exit(-1);



	# Version
	if (arguments["version"]):
		sys.stdout.write("Version {0:s}".format(".".join([ str(v) for v in version_info ])));
		return 0;

	if (arguments["help"]):
		# Usage info
		usage(arguments_descriptor, sys.stdout);
		return 0;



	# Parse commands
	commands = [];

	# Unmount
	if (arguments["unmount"]):
		if (
			arguments["path"] is None
		):
			# Error
			sys.stderr.write("\"unmount\" command requires a path\n");
			return -1;

		commands.append("unmount");

	# Delete
	if (arguments["delete"]):
		if (
			arguments["path"] is None
		):
			# Error
			sys.stderr.write("\"delete\" command requires a path\n");
			return -1;

		# Add command
		commands.append("delete");

	# Create
	if (arguments["create"]):
		if (
			arguments["path"] is None
		):
			# Error
			sys.stderr.write("\"create\" command requires a path\n");
			return -1;

		if (
			arguments["size"] is None
		):
			# Error
			sys.stderr.write("\"create\" command requires a size\n");
			return -1;

		# Add command
		commands.append("create");

	# Mount
	if (arguments["mount"]):
		if (
			arguments["path"] is None
		):
			# Error
			sys.stderr.write("\"mount\" command requires a path\n");
			return -1;

		if (
			arguments["letter"] is None
		):
			# Error
			sys.stderr.write("\"mount\" command requires a drive letter\n");
			return -1;

		# Add command
		commands.append("mount");



	# Usage?
	if (len(commands) == 0):
		usage(arguments_descriptor, sys.stderr);
		return -2;



	# Execute
	return_code = 0;
	for command in commands:
		# Command execution
		ret = None;
		if (command == "unmount"):
			ret = command_unmount(arguments["path"], arguments["letter"]);
		elif (command == "delete"):
			ret = command_delete(arguments["path"]);
		elif (command == "create"):
			size = int(arguments["size"], 10);
			ret = command_create(arguments["path"], size, arguments["label"], arguments["file-system"]);
		elif (command == "mount"):
			ret = command_mount(arguments["path"], arguments["letter"]);

		# Error
		if (ret is not None):
			sys.stderr.write("{0:s} error: {1:s}\n".format(command, ret));
			if (arguments["stop-on-error"]):
				return 2;
			return_code = 1;



	# Done
	return return_code;



# Execute
if (__name__ == "__main__"): sys.exit(main());

