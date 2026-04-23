import os
import subprocess
import threading


class PackingProject:
    def get_python_installations(self):
        try:
            result = subprocess.run(
                ["cmd.exe", "/c", "where python"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            return lines
        except Exception:
            return []

    def install_requirements(self, python_location, python_lib):
        def run():
            print("\n.............................................")
            print("Packages installation has started\n")
            requirements = os.path.join(python_lib, "requirements.txt")
            python_exe = os.path.join(python_location, "python.exe")
            try:
                subprocess.run(
                    [python_exe, "-m", "pip", "install", "-r", requirements],
                    cwd=python_location
                )
            except Exception as ex:
                print(f"Error installing packages: {ex}")
            finally:
                print("\nPackages have been correctly installed")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def call_python(self, python_location, python_lib, game, action, args, message):
        def run():
            print("\n.............................................")
            print(f"{message} has started\n")
            python_exe = os.path.join(python_location, "python.exe")
            tools_executable = os.path.join(python_lib, "ToolsTales_Executable.py")
            cmd = f'"{python_exe}" "{tools_executable}" --game {game} {action} {args}'
            try:
                subprocess.run(cmd, shell=True, cwd=python_lib)
                print(f"\n{message} has completed")
            except Exception as ex:
                print(f"Error: {ex}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread
