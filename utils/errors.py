from discord.ext.commands import CommandError

class GammaBaseException(CommandError):
    pass
    
class GuildBlacklistedError(GammaBaseException):
    def __init__(self, guild):
        super().__init__("You are blacklisted from running commands in `{guild}`. Please ask a moderator to unblacklist you if you feel you have been unjustly blacklisted.".format(**locals()))

class GlobalBlacklistedError(GammaBaseException):
    def __init__(self):
        super().__init__("You are globally blacklisted from running these commands. Please contact `Xua#9307` if you wish to appeal to this.")

class BadUpload(GammaBaseException):
    def __init__(self):
        super().__init__("The image or link you specified was not a valid PNG/JPEG/GIF image.")
        
class MissingUpload(GammaBaseException):
    def __init__(self):
        super().__init__("You did not upload either an image attachment or a link.")
        
class HTTPException(GammaBaseException):
    def __init__(self, code, message):
        super().__init__(f"Command failed with error code {code}: {message}")