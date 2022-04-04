import functools
import json
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import packaging.version
from deepdiff.model import PrettyOrderedSet
from openff.utilities import MissingOptionalDependency, requires_package
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


class DeepDiffEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PrettyOrderedSet):
            return [*obj]

        return json.JSONEncoder.default(self, obj)


def download_file(url: str, description: str, output_path: Path):
    """Downloads a file while showing a pretty ``rich`` progress bar."""

    with Progress(
        TextColumn(f"[bold blue]{description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        transient=False,
    ) as progress:

        task_id = progress.add_task("download", start=False)

        with urlopen(url) as response:

            progress.update(task_id, total=int(response.info()["Content-length"]))

            with output_path.open("wb") as file:

                progress.start_task(task_id)

                for data in iter(functools.partial(response.read, 32768), b""):

                    file.write(data)
                    progress.update(task_id, advance=len(data))


def download_file_contents(url, description) -> str:
    """Downloads a file while showing a pretty ``rich`` progress bar and returns its
    string contents."""

    with NamedTemporaryFile() as file:

        download_path = Path(file.name)

        download_file(url, description, download_path)

        with download_path.open("r") as file:
            return file.read()


@contextmanager
@requires_package("openeye.oechem")
def _oe_capture_warnings():  # pragma: no cover

    from openeye import oechem

    output_stream = oechem.oeosstream()

    oechem.OEThrow.SetOutputStream(output_stream)
    oechem.OEThrow.Clear()

    yield

    oechem.OEThrow.SetOutputStream(oechem.oeerr)


@contextmanager
def capture_toolkit_warnings():  # pragma: no cover
    """A convenience method to capture and discard any warning produced by external
    cheminformatics toolkits including the very very very very very verbose OpenFF
    toolkit. This should be used with extreme caution and is only really intended for
    use when processing tens of thousands of molecules at once.
    """

    import logging
    import warnings

    warnings.filterwarnings("ignore")

    openff_logger_level = logging.getLogger("openff.toolkit").getEffectiveLevel()
    logging.getLogger("openff.toolkit").setLevel(logging.ERROR)

    try:
        with _oe_capture_warnings():
            yield
    except MissingOptionalDependency:
        yield

    logging.getLogger("openff.toolkit").setLevel(openff_logger_level)


def use_openff_units() -> bool:
    from openff.toolkit import __version__ as toolkit_version

    return (
        packaging.version.parse(toolkit_version) >= packaging.version.parse("0.11.0")
        or "+" in toolkit_version
    )
