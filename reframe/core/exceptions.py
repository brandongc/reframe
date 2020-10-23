# Copyright 2016-2020 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

#
# Base regression exceptions
#

import inspect
import os
import traceback
import warnings
import sys

import reframe.utility as utility


class ReframeBaseError(BaseException):
    '''Base exception for any ReFrame error.

    This exception base class offers a specialized :func:`__str__` method that
    concatenates the messages of a chain of exceptions by inspecting their
    :py:data:`__cause__` field. For example, the following piece of code will
    print ``error message 2: error message 1``:

    .. code-block:: python

       from reframe.core.exceptions import *


       def foo():
           raise ReframeError('error message 1)

       def bar():
           try:
               foo()
           except ReframeError as e:
               raise ReframeError('error message 2') from e

      if __name__ == '__main__':
          try:
              bar()
          except Exception as e:
              print(e)

    '''

    def __init__(self, *args):
        self._message = str(args[0]) if args else None

    @property
    def message(self):
        return self._message

    def __str__(self):
        ret = self._message or ''
        if self.__cause__ is not None:
            ret += ': ' + str(self.__cause__)

        return ret


class ReframeError(ReframeBaseError, Exception):
    '''Base exception for soft errors.

    Soft errors may be treated by simply printing the exception's message and
    trying to continue execution if possible.
    '''


class ReframeFatalError(ReframeBaseError):
    '''A fatal framework error.

    Execution must be aborted.
    '''


class ReframeSyntaxError(ReframeError):
    '''Raised when the syntax of regression tests is incorrect.'''


class RegressionTestLoadError(ReframeError):
    '''Raised when the regression test cannot be loaded.'''


class NameConflictError(RegressionTestLoadError):
    '''Raised when there is a name clash in the test suite.'''


class TaskExit(ReframeError):
    '''Raised when a regression task must exit the pipeline prematurely.'''


class TaskDependencyError(ReframeError):
    '''Raised inside a regression task by the runtime when one of its
    dependencies has failed.
    '''


class AbortTaskError(ReframeError):
    '''Raised by the runtime inside a regression task to denote that it has
    been aborted due to an external reason (e.g., keyboard interrupt, fatal
    error in other places etc.)
    '''


class ConfigError(ReframeError):
    '''Raised when a configuration error occurs.'''


class LoggingError(ReframeError):
    '''Raised when an error related to logging has occurred.'''


class EnvironError(ReframeError):
    '''Raised when an error related to an environment occurs.'''


class SanityError(ReframeError):
    '''Raised to denote an error in sanity checking.'''


class PerformanceError(ReframeError):
    '''Raised to denote an error in performance checking, e.g., when a
    performance reference is not met.'''


class PipelineError(ReframeError):
    '''Raised when a condition prevents the regression test pipeline to
    continue and the error may not be described by another more specific
    exception.
    '''


class ReframeForceExitError(ReframeError):
    '''Raised when ReFrame execution must be forcefully ended,
    e.g., after a SIGTERM was received.
    '''


class StatisticsError(ReframeError):
    '''Raised to denote an error in dealing with statistics.'''


class BuildSystemError(ReframeError):
    '''Raised when a build system is not configured properly.'''


class ContainerError(ReframeError):
    '''Raised when a container platform is not configured properly.'''


class BuildError(ReframeError):
    '''Raised when a build fails.'''

    def __init__(self, stdout, stderr):
        super().__init__()
        self._message = (
            "standard error can be found in `%s', "
            "standard output can be found in `%s'" % (stderr, stdout)
        )


class SpawnedProcessError(ReframeError):
    '''Raised when a spawned OS command has failed.'''

    def __init__(self, args, stdout, stderr, exitcode):
        super().__init__()

        if isinstance(args, str):
            self._command = args
        else:
            self._command = ' '.join(args)

        self._stdout = stdout
        self._stderr = stderr
        self._exitcode = exitcode

        # Format message
        lines = [
            f"command '{self.command}' failed with exit code {self.exitcode}:"
        ]
        lines.append('=== STDOUT ===')
        if stdout:
            lines.append(stdout)

        lines.append('=== STDERR ===')
        if stderr:
            lines.append(stderr)

        self._message = '\n'.join(lines)

    @property
    def command(self):
        '''The command that the spawned process tried to execute.'''
        return self._command

    @property
    def stdout(self):
        '''The standard output of the process as a string.'''
        return self._stdout

    @property
    def stderr(self):
        '''The standard error of the process as a string.'''
        return self._stderr

    @property
    def exitcode(self):
        '''The exit code of the process.'''
        return self._exitcode


class SpawnedProcessTimeout(SpawnedProcessError):
    '''Raised when a spawned OS command has timed out.'''

    def __init__(self, args, stdout, stderr, timeout):
        super().__init__(args, stdout, stderr, None)
        self._timeout = timeout

        # Format message
        lines = [f"command '{self.command}' timed out after {self.timeout}s:"]
        lines.append('=== STDOUT ===')
        if self._stdout:
            lines.append(self._stdout)

        lines.append('=== STDERR ===')
        if self._stderr:
            lines.append(self._stderr)

        self._message = '\n'.join(lines)

    @property
    def timeout(self):
        '''The timeout of the process.'''
        return self._timeout


class JobSchedulerError(ReframeError):
    '''Raised when a job scheduler encounters an error condition.'''


class JobError(ReframeError):
    '''Raised for job related errors.'''

    def __init__(self, msg=None, jobid=None):
        message = '[jobid=%s]' % jobid
        if msg:
            message += ' ' + msg

        super().__init__(message)
        self._jobid = jobid

    @property
    def jobid(self):
        '''The job ID of the job that encountered the error.'''
        return self._jobid


class JobBlockedError(JobError):
    '''Raised by job schedulers when a job is blocked indefinitely.'''


class JobNotStartedError(JobError):
    '''Raised when trying an operation on a unstarted job.'''


class DependencyError(ReframeError):
    '''Raised when a dependency problem is encountered.'''


class ReframeDeprecationWarning(DeprecationWarning):
    '''Warning raised for deprecated features of the framework.'''


warnings.filterwarnings('default', category=ReframeDeprecationWarning)


def user_frame(exc_type, exc_value, tb):
    '''Return a user frame from the exception's traceback.

    As user frame is considered the first frame that is outside from
    :mod:`reframe` module.

    :returns: A frame object or :class:`None` if no user frame was found.

    :meta private:

    '''
    if not inspect.istraceback(tb):
        raise ValueError('could not retrieve frame: argument not a traceback')

    for finfo in reversed(inspect.getinnerframes(tb)):
        relpath = os.path.relpath(finfo.filename, sys.path[0])
        if relpath.split(os.sep)[0] != 'reframe':
            return finfo

    return None


def is_severe(exc_type, exc_value, tb):
    '''Check if exception is a severe one.'''
    soft_errors = (ReframeError,
                   ConnectionError,
                   FileExistsError,
                   FileNotFoundError,
                   IsADirectoryError,
                   KeyboardInterrupt,
                   NotADirectoryError,
                   PermissionError,
                   TimeoutError)
    if isinstance(exc_value, soft_errors):
        return False

    # Treat specially type and value errors
    type_error  = isinstance(exc_value, TypeError)
    value_error = isinstance(exc_value, ValueError)
    frame = user_frame(exc_type, exc_value, tb)
    if (type_error or value_error) and frame is not None:
        return False

    return True


def what(exc_type, exc_value, tb):
    '''A short description of the error.'''

    if exc_type is None:
        return ''

    reason = utility.decamelize(exc_type.__name__, ' ')

    # We need frame information for user type and value errors
    frame = user_frame(exc_type, exc_value, tb)
    user_type_error  = isinstance(exc_value, TypeError)  and frame
    user_value_error = isinstance(exc_value, ValueError) and frame
    if isinstance(exc_value, KeyboardInterrupt):
        reason = 'cancelled by user'
    elif isinstance(exc_value, AbortTaskError):
        reason = f'aborted due to {type(exc_value.__cause__).__name__}'
    elif user_type_error or user_value_error:
        relpath = os.path.relpath(frame.filename)
        source = ''.join(frame.code_context)
        reason += f': {relpath}:{frame.lineno}: {exc_value}\n{source}'
    else:
        if str(exc_value):
            reason += f': {exc_value}'

    return reason


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
