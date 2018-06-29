#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from bincrafters import build_template_default


if __name__ == "__main__":

    os.environ["CONAN_BUILD_POLICY"] = "missing"
    
    builder = build_template_default.get_builder(pure_c=False)

    # Revert this change once boost is available for other than libstdc++11.    
    modified_builds = []
    for settings, options, env_vars, build_requires, reference in builder.items:
        if settings["compiler.libcxx"] != "libstdc++":
            modified_builds.append([settings, options, env_vars, build_requires])
    builder.builds = modified_builds

    builder.run()
