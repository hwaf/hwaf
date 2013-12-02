#!/usr/bin/env python
'''Feature to install a Python package via its setup.py file.

This feature relies on the "unpack" step to have run.  It is assumed
the suite is installing Python or that python_install_dir is
explicitly set.

It produces the "build" and "install" steps.

Note, these steps run in the source directory.  A "prepare" step is not required.

'''

from waflib.TaskGen import feature

import orch.features
orch.features.register_defaults(
    'pypackage',
    build_cmd = 'python setup.py build',
    build_cmd_options = '',
    build_target = '',
    build_target_path = '{source_unpacked_path}/{build_target}',
    
    install_cmd = 'python setup.py install --prefix={python_install_dir}',
    install_cmd_options = '',
    install_target = '',
    install_target_path = '{python_install_dir}/{install_target}',
    
)

@feature('pypackage')
def feature_pypackage(tgen):
    
    # dummy prepare step, for feature_patch's benefit and "depends = prepare:xxx_install"
    tgen.step('prepare',
              rule = "/bin/true",
              source = tgen.control_node('unpack'),
              target = tgen.control_node('prepare'))

    tgen.step('build',
              rule = tgen.worch.format('{build_cmd} {build_cmd_options}'),
              source = tgen.control_node('prepare'),
              target = tgen.worch.build_target_path,
              cwd = tgen.worch.source_unpacked_path)

    tgen.step('install',
              rule = tgen.worch.format('{install_cmd} {install_cmd_options}'),
              source = [tgen.worch.build_target_path, tgen.control_node('build')],
              target = tgen.make_node(tgen.worch.install_target_path),
              cwd = tgen.worch.source_unpacked_path)
