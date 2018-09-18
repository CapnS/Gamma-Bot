from discord.ext.commands import BadArgument


class Argument:
    def __init__(self, *, type=str, default=""):
        self.type = type
        self.default = default


class ArgParser:
    def __init__(self, *, flags: dict, silent: bool=False):
        """
        Creates a new Argument Parser for the specified command.

        |Parameters|
        flags -> dict # {"arg1": bool, "arg2": int, "arg3": str}
        Required to create the new parser.

        silent -> bool # True, False
        Decides whether to ignore invalid flags. Defaults to False.
        """
        self.flags = flags
        self.silent = silent

    def parse(self, data: str):
        """
        Takes a string and converts it to a dict of arguments.
        "--arg1 --arg2=no --arg3=5 --arg4=say"
        The above will be converted to:
        {"arg1": True, "arg2": False, "arg3": 5, "arg4": "say"}

        |Parameters|
        data -> str # as above
        Required for parsing. It must follow a format similar to standard posix flags.
        --flag=etc or --flag

        |Returns|
        A dict containing each of the arguments, assuming it completed successfully.
        """
        if not data:
            ret = {}
            for arg, val in self.flags.items():
                if val is str:
                    ret.setdefault(arg, "")
                elif val is int:
                    ret.setdefault(arg, 0)
                elif val is bool:
                    ret.setdefault(arg, False)
            return ret
        alpha = data.lstrip("--").split(" --")  # split each argument into its own values ("arg1=etc", "arg2=5", ...)
        # if slient mode is not enabled, we will begin making sure no invalid flags were passed.
        if not self.silent:
            for arg in alpha:
                if arg.split("=")[0] not in self.flags.keys():
                    raise ValueError(f"Unknown flag '{arg}'")
        # being translating each arg and value into a dict
        ret = {}
        for arg in alpha:
            split = arg.split("=")
            if len(split) == 1:
                key, value = split[0], "true"
            else:
                key, value = split
            if value.isdigit():
                value = int(value)
            else:
                if value in ("yes", "y", "on", "true", "enable"):
                    value = True
                elif value in ("no", "n", "off", "false", "disable"):
                    value = False
            # here, we want to filter bad arguments
            try:
                if not isinstance(value, self.flags.get(key)):
                    raise BadArgument(f"Invalid value '{value}' for flag '{key}'")
            except TypeError:  # filter out bad arguments if silent mode if on
                continue
            # all checks are done for this value, add it to the final product
            ret.setdefault(key, value)
        #  begin to add the default arguments for every missed flag
        for flag in self.flags.keys():  # loop over every flag
            if not ret.get(flag):  # if the flag isnt in the return dict
                val = self.flags.get(flag)  # retrieve the type required
                if val is str:
                    ret.setdefault(flag, "")
                elif val is int:
                    ret.setdefault(flag, 0)
                elif val is bool:
                    ret.setdefault(flag, False)
        return ret