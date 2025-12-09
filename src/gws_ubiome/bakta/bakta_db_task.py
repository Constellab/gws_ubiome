#!/usr/bin/env python3
import os
from typing import Final
from gws_core import (
    ConfigParams, ConfigSpecs,
    OutputSpec, OutputSpecs, Folder,
    ShellProxy, Task, TaskInputs, TaskOutputs,
    StrParam, BoolParam, task_decorator
)

from ..base_env.Bakta_env import BaktaShellProxyHelper  # keep your helper import

@task_decorator(
    "BaktaDB",
    human_name="Build/Update Bakta Database",
    short_description="Download or update the mandatory Bakta database (full or light)"
)
class BaktaDBTask(Task):

    input_specs = {}
    output_specs: Final[OutputSpecs] = OutputSpecs({
        "bakta_db_folder": OutputSpec(Folder, human_name="Bakta DB folder")
    })

    config_specs: Final[ConfigSpecs] = ConfigSpecs({
        "db_type": StrParam(
            default_value="full",
            allowed_values=["full", "light"],
            short_description="Database type to download"
        ),
        "force_update": BoolParam(
            default_value=False,
            short_description="If True, run bakta_db update even if DB markers are found"
        )
    })

    def _db_is_present(self, db_dir: str) -> bool:
        """
        Heuristic: Bakta DB typically contains a VERSION file and a 'db' directory
        with SQLite & data files. Consider the DB present if we can find at least
        two of the expected markers directly under db_dir.
        """
        if not os.path.isdir(db_dir):
            return False

        markers_found = 0
        # Marker 1: VERSION file
        if os.path.isfile(os.path.join(db_dir, "VERSION")):
            markers_found += 1

        # Marker 2: sqlite database (location may vary with versions)
        if os.path.isfile(os.path.join(db_dir, "bakta.sqlite")):
            markers_found += 1

        # Marker 3: 'db' subdir with content
        db_subdir = os.path.join(db_dir, "db")
        if os.path.isdir(db_subdir) and any(os.scandir(db_subdir)):
            markers_found += 1

        return markers_found >= 2

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        db_type: str = params["db_type"]
        force_update: bool = params["force_update"]

        shell: ShellProxy = BaktaShellProxyHelper.create_proxy(self.message_dispatcher)
        output_dir = os.path.join(shell.working_dir, f"bakta_db_{db_type}")
        os.makedirs(output_dir, exist_ok=True)

        # If DB already exists and not forcing update, skip
        if self._db_is_present(output_dir) and not force_update:
            print(f"[BaktaDB] Database appears present in {output_dir}; skipping download.")
            return {"bakta_db_folder": Folder(output_dir)}

        # Otherwise, download (recommended by Bakta docs)
        cmd = f"bakta_db download --output {output_dir} --type {db_type}"
        print(f"[BaktaDB] {cmd}")
        if shell.run(cmd, shell_mode=True) != 0:
            raise RuntimeError("Bakta DB download failed")

        # Optional: update in place
        if force_update:
            up_cmd = f"bakta_db update --db {output_dir}"
            print(f"[BaktaDB] {up_cmd}")
            shell.run(up_cmd, shell_mode=True)

        return {"bakta_db_folder": Folder(output_dir)}
