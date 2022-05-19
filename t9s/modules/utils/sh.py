import subprocess


class SubProcessHelpers:
    @staticmethod
    def run_proc(cmd):
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        process.wait()
        return process, out, err
