import click
import signal
import sys
import time


class TimeoutTimer:
    """
    A convenient wrapper for triggering a TimeoutError after a given time.

    There should only be a single TimeoutTimer object at a given time.
    """

    def __init__(self, initial_timeout):
        self._initial_timeout = initial_timeout

    def __enter__(self):
        """
        Start the timer.
        :return: This timer
        """

        def handler(signum, frame):
            raise TimeoutError()

        signal.signal(signal.SIGALRM, handler)

        self._start_time = time.time()
        if self._initial_timeout > 0:
            signal.setitimer(signal.ITIMER_REAL, self._initial_timeout)
        return self

    def recap_timeout(self, new_timeout):
        """
        Set the new timeout of this Timer, measured from the start of the timer,
        if the new timeout would trigger sooner.

        :param new_timeout: The new timeout to set (0 indicates cancel)
        :return: None
        """
        if new_timeout == 0:
            self.cancel()
            return

        new_time_remaining = self._start_time + new_timeout - time.time()
        if new_time_remaining < 0:
            self.cancel()
            raise TimeoutError()
        elif signal.getitimer(signal.ITIMER_REAL)[0] > new_time_remaining:
            signal.setitimer(signal.ITIMER_REAL, new_time_remaining)

    def reset_timeout(self, new_timeout):
        """
        Set the new timeout of this Timer, measured from the start of the timer.

        :param new_timeout: The new timeout to set (0 indicates cancel)
        :return: None
        """
        if new_timeout == 0:
            self.cancel()
            return

        new_time_remaining = self._start_time + new_timeout - time.time()
        if new_time_remaining < 0:
            self.cancel()
            raise TimeoutError()
        else:
            signal.setitimer(signal.ITIMER_REAL, new_time_remaining)

    def __exit__(self, exit_type, value, traceback):
        """
        Cancel the timer.
        :return: None
        """
        signal.setitimer(signal.ITIMER_REAL, 0)

    def cancel(self):
        """
        Cancel the timer.
        :return: None
        """
        signal.setitimer(signal.ITIMER_REAL, 0)


class Stopwatch:
    """
    A stopwatch for easy measurement of elapsed time, optionally split into intervals.
    """

    def __init__(self):
        self.__start = time.time()
        self.__interval_start = self.__start
        self.__records = {}

    def record_interval(self, name):
        """
        Record the time elapsed since the end of the last interval.

        :param name: The name of the record to make
        :return: None
        """
        interval_end = time.time()
        self.__records[name] = interval_end - self.__interval_start
        self.__interval_start = interval_end

    def record_total(self, name):
        """
        Record the time elapsed since the creation of this stopwatch.

        :param name: The name of the record to make
        :return: None
        """
        self.__records[name] = time.time() - self.__start

    def elapsed_time(self):
        """
        Return the time elapsed since the creation of this stopwatch.
        :return: The time elapsed, in seconds
        """

        return time.time() - self.__start

    @property
    def records(self):
        return dict(self.__records)


class KeyValueOutput(click.File):
    """
    A convenient wrapper class for click.File that provides a nice interface for key/value pairs.
    Additionally, allow outputting to stdout if '-' is provided as the argument,
    or stderr is '!' is provided as the argument.
    """

    def convert(self, value, param, ctx):
        if value in (b"-", "-"):

            class PrintWrapper:
                def write(self, s):
                    print(s, end="")

            result = PrintWrapper()
        elif value in (b"!", "!"):

            class StderrWrapper:
                def write(self, s):
                    print(s, file=sys.stderr, end="")

            result = StderrWrapper()
        else:
            result = click.File.convert(self, value, param, ctx)
        result.output_pair = lambda key, val: result.write(key + ": " + str(val) + "\n")
        return result


class TypedChoice(click.Choice):
    """
    A modified version of click.Choice that allows the choice options to be arbitrary objects.
    The argument is compared against the string representation of each object; if it matches,
    then the object is returned.

    As with click.Choice, you should only pass a list or tuple of choices. Other iterables
    (like generators) may lead to surprising results.

    :param case_sensitive: Set to false to make choices case insensitive. Defaults to true.
    """

    name = "typedchoice"

    def __init__(self, choices, case_sensitive=True):
        self.object_choices = choices

        click.Choice.__init__(
            self, list(map(str, choices)), case_sensitive=case_sensitive
        )

    def convert(self, value, param, ctx):
        # Exact match
        if value in self.choices:
            return self.object_choices[self.choices.index(value)]

        # Match through normalization and case sensitivity
        # first do token_normalize_func, then lowercase
        # preserve original `value` to produce an accurate message in
        # `self.fail`
        normed_value = value
        normed_choices = self.choices

        if ctx is not None and ctx.token_normalize_func is not None:
            normed_value = ctx.token_normalize_func(value)
            normed_choices = [
                ctx.token_normalize_func(choice) for choice in self.choices
            ]

        if not self.case_sensitive:
            normed_value = normed_value.lower()
            normed_choices = [choice.lower() for choice in normed_choices]

        if normed_value in normed_choices:
            return self.object_choices[normed_choices.index(normed_value)]

        self.fail(
            "invalid choice: %s. (choose from %s)" % (value, ", ".join(self.choices)),
            param,
            ctx,
        )

    def __repr__(self):
        return "TypedChoice(%r)" % list(self.choices)


class TaggedChoice(click.Choice):
    """
    A modified version of click.Choice that allows the choice options to be provided as a
    dictionary. The argument is compared against the keys of the dictionary; if it matches,
    then the corresponding value is returned.

    :param case_sensitive: Set to false to make choices case insensitive. Defaults to true.
    """

    name = "taggedchoice"

    def __init__(self, options, case_sensitive=True):
        self.options = options

        click.Choice.__init__(self, list(options.keys()), case_sensitive=case_sensitive)

    def convert(self, value, param, ctx):
        # Exact match
        if value in self.options:
            return self.options[value]

        # Match through normalization and case sensitivity
        # first do token_normalize_func, then lowercase
        # preserve original `value` to produce an accurate message in
        # `self.fail`
        def normalize(val):
            if ctx is not None and ctx.token_normalize_func is not None:
                val = ctx.token_normalize_func(val)
            if not self.case_sensitive:
                val = val.lower()
            return val

        normalized_value = normalize(value)
        for key in self.options:
            if normalize(key) == normalized_value:
                return self.options[key]

        self.fail(
            "invalid choice: %s. (choose from %s)" % (value, ", ".join(self.options)),
            param,
            ctx,
        )

    def __repr__(self):
        return "TypedChoice(%r)" % list(self.choices)


def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
