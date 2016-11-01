class WrappedClosure(object):
    """This class is a decorator whose purpose is to mark methods
    that wrap the actual methods in closures, to be unwrapped later."""

    # __init__ ############################################
    def __init__(self, method):
        """Constructor.  Stores a method that contains a closure.

        Best practices for the method:
        The method should be written such that the closure has the same name
        as the containing method.  This is not necessary, but the return value
        of the containing method will be rebound to the containing method's
        name after a call to unwrap_all().
        """
        if not callable(method):
            raise TypeError("method must be a callable object.")
        self.__method = method

    # __call__ ############################################
    def __call__(self):
        """Calls the stored method."""
        return self.__method()

    # unwrap_all ##########################################
    @classmethod
    def unwrap_all(cls, scope):
        """This method is to be called after all instances of this class
        have been declared (i.e. all methods have been decorated by this
        class).  This method looks for all variables in the scope you supply
        (usually locals()) that are instances of this class, calls these
        instances as functions, and reassigns the return value to the same
        name.
        """

        # Examine all variables.
        for variable in scope:

            # I'm checking the exact type on purpose.
            # What if this class were subclassed and different
            # behavior was desired for each differing type?
            #
            # Also, by design, I want each subclass to handle their own types
            # individually.
            if type(scope[variable]) is cls:
                scope[variable] = scope[variable]() # Reassign the return value to the same name.
