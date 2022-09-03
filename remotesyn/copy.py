import shutil

class copy_local:
    def __init__(self, config):
        self.config = config

    def copy_from_dir(self, src, dst):
        pass
        # Nothing to do here since we are working in local build

    def copy_to_dir(self, src, dst):
        shutil.copy(src, dst)

class copy_remote:
    def __init__(self, config):
        self.config = config

    def copy_from_dir(self, src, dst):
        print("ERROR: Not yet implemented")

    def copy_to_dir(self, src, dst):
        print("ERROR: Not yet implemented")