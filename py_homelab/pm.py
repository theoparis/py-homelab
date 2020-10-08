import subprocess
from os import path
from git import Repo
from subprocess import Popen, PIPE, CalledProcessError
import atexit
import logging
import os
import tempfile
import shlex
from io import StringIO
from .map import Map

logging.basicConfig()
logger = logging.getLogger("ProcessManager")


def run_shell_command(command_line, cwd, output=False):
    command_line_args = shlex.split(command_line)

    logger.info('Subprocess: "' + command_line + '"')

    command_line_process = subprocess.Popen(
        command_line_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        shell=True
    )

    if output:
        process_output, _ = command_line_process.communicate()

        # process_output is now a string, not a file,
        # you may want to do:
        process_output = StringIO(str(process_output))
        process_output.close()

    # no exception was raised
    logger.info('Subprocess finished')

    return Map({"status": True, "process": command_line_process})


class ProcessManager():
    def __init__(self, base_dir=os.getcwd()):
        self.base_dir = base_dir
        self.processes = Map()
        atexit.register(self.cleanup)

    def clone(self, app_path: str, url: str, branch: str):
        repo = None
        # Clone app if it doesn't exist
        if not path.exists(app_path):
            repo = Repo.clone_from(url, app_path, branch=branch)
        else:
            repo = Repo(app_path)

        assert repo.__class__ is Repo     # clone an existing repository
        current = repo.head.commit
        try:
            repo.remotes.origin.fetch()
        except:
            logger.error("Could not fetch remote status for repository!")
        # Check if remote has new changes to pull into local app repository
        if current != repo.head.commit:
            logger.info("Repository changed on remote, updating...")
            repo.remotes.origin.pull()

    def cleanup(self):
        timeout_sec = 5
        for p in self.processes:  # list of your processes
            p_sec = 0
            for second in range(timeout_sec):
                if p.poll() == None:
                    time.sleep(1)
                    p_sec += 1
            if p_sec >= timeout_sec:
                p.kill()  # supported from python 2.6
        print('cleaned up!')

    def deploy(self, app):
        app_path = os.path.join(self.base_dir, "data", app.name)

        self.clone(app_path, app.repo.url, app.repo.branch or "master")

        if app.type == "node":
            run_shell_command('npm install', app_path)
            try:
                run_shell_command('npm run build', app_path)
            except Exception as err:
                logger.info(
                    f"Failed to build app {app.name}. This could mean that you did not specify a build command - this is ok.")
                return {"status": False, "message": str(err)}
            try:
                # Stop app if it is already running
                try:
                    self.processes[app.name].kill()
                except:
                    logger.info("Could not kill existing process.")

                result = run_shell_command(
                    "npm run start", app_path)
                self.processes[app.name] = result.process
                return {"status": result.status, "message": f"Successfully deployed app {app.name}"}
            except Exception as err:
                logger.error(
                    f"Failed to start app {app.name}: {str(err)}")
                return {"status": False, "message": str(err)}
