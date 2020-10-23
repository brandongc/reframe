import contextlib
import inspect
import os
import warnings

from reframe.core.exceptions import ReframeFatalError


class ReframeDeprecationWarning(DeprecationWarning):
    '''Warning raised for deprecated features of the framework.'''


warnings.filterwarnings('default', category=ReframeDeprecationWarning)


_format_warning_orig = warnings.formatwarning


def _format_warning(message, category, filename, lineno, line=None):
    import reframe.core.runtime as rt
    import reframe.utility.color as color

    if category != ReframeDeprecationWarning:
        return _format_warning_orig(message, category, filename, lineno, line)

    if line is None:
        # Read in the line from the file
        with open(filename) as fp:
            try:
                line = fp.readlines()[lineno-1]
            except IndexError:
                line = '<no line information>'

    # Use a relative path
    filename = os.path.relpath(filename)
    message = f'{filename}:{lineno}: WARNING: {message}\n{line}\n'

    # Ignore coloring if runtime has not been initialized; this can happen
    # when generating the documentation of deprecated APIs
    with contextlib.suppress(ReframeFatalError):
        if rt.runtime().get_option('general/0/colorize'):
            message = color.colorize(message, color.YELLOW)

    return message


warnings.formatwarning = _format_warning


def user_deprecation_warning(message):
    '''Raise a deprecation warning at the user stack frame that eventually
    calls this function.

    As "user stack frame" is considered a stack frame that is outside the
    :py:mod:`reframe` base module.
    '''

    # Unroll the stack and issue the warning from the first stack frame that is
    # outside the framework.
    stack_level = 1
    for s in inspect.stack():
        module = inspect.getmodule(s.frame)
        if module is None or not module.__name__.startswith('reframe'):
            break

        stack_level += 1

    warnings.warn(message, ReframeDeprecationWarning, stacklevel=stack_level)
