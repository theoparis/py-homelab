import subprocess
import atexit
import os
import tempfile
import shlex
import time
import getpass
from os import path
from git import Repo
from subprocess import Popen, PIPE, CalledProcessError
from io import StringIO
from throw_out_py import Map, create_logger


def run_shell_command(command_line, cwd, logger=create_logger(name="ProcessManager"), block=True, output=False, env=os.environ.copy()):
    command_line_args = shlex.split(command_line)

    logger.info('Subprocess: "' + command_line + '"')

    command_line_process = subprocess.Popen(
        command_line_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        shell=True,
        env=env
    )

    if block:
        process_output, _ = command_line_process.communicate()
        if output:
            logger.info(str(process_output))
    # no exception was raised
    logger.info('Subprocess finished')

    return Map({"status": True, "process": command_line_process})


class ProcessManager():
    def __init__(self, base_dir=os.getcwd()):
        self.base_dir = base_dir
        self.logs_dir = path.join(self.base_dir, "logs")

        self.processes = Map()
        atexit.register(self.cleanup)

    def clone(self, app_path: str, url: str, branch: str, logger=create_logger(name="ProcessManager")):
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
        app_path = path.join(self.base_dir, "data", app.name)

        log_dir = path.join(self.logs_dir, app.name)
        if not path.exists(log_dir):
            os.umask(0)
            os.makedirs(log_dir)
        logger = create_logger(path=path.join(
            log_dir, "log.txt"), name="ProcessManager")

        self.clone(app_path, app.repo.url,
                   app.repo.branch or "master", logger=logger)

        if app.type == "node":
            run_shell_command('npm install', app_path, logger=logger)
            try:
                run_shell_command('npm run build', app_path, logger=logger)
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

                app_env = os.environ.copy()
                app_env["PORT"] = str(app.port or 3000)
                result = run_shell_command(
                    "npm run start", app_path, block=False, output=True, logger=logger, env=app_env)
                self.processes[app.name] = result.process
                logger.info(f"Successfully deployed app {app.name}")
                return {"status": result.status, "message": f"Successfully deployed app {app.name}"}
            except Exception as err:
                logger.error(
                    f"Failed to start app {app.name}: {str(err)}")
                return {"status": False, "message": str(err)}


pm = ProcessManager()
