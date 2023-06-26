class JLError:
    """
    Class representing error returned by JLFileHandler.
    """
    def __init__(self, message: str) -> None:
        """
        Constructor for JLError
        :param message: The details of the error
        """
        self.message = message

    def __str__(self):
        """
        String representation of the error.
        :return: Instance of JLError class
        """
        return self.message
